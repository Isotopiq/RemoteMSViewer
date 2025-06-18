using System;
using System.Threading.Tasks;
using Thermo.Interfaces.InstrumentAccess_V1;
using Thermo.Interfaces.InstrumentAccess_V1.Control;
using Thermo.Interfaces.InstrumentAccess_V1.Control.Acquisition;
using Thermo.Interfaces.InstrumentAccess_V1.Control.Methods;
using Thermo.Interfaces.InstrumentAccess_V1.Control.InstrumentValues;
using Thermo.Interfaces.InstrumentAccess_V1.Control.Scans;
using Thermo.Interfaces.InstrumentAccess_V1.MsScanContainer;
using Thermo.Interfaces.ExplorisAccess_V1;
using System.IO;
using System.Reflection;
using System.Xml;
using Microsoft.Win32;

namespace EddysExploris
{
    public class InstrumentConnection
    {
        private IInstrumentAccess _instrumentAccess;
        private IMsScanContainer _scans;
        private bool _isConnected;

        public event EventHandler<IMsScan> OnNewScan;
        public event EventHandler<bool> OnConnectionChanged;

        public InstrumentConnection()
        {
            _isConnected = false;
        }

        private IExplorisInstrumentAccessContainer GetApiInstance()
        {
            const string DefaultBasePath = "Thermo\\Exploris";
            const string DefaultRegistry = "SOFTWARE\\Thermo Exploris";
            const string XmlRoot = "DataSystem";
            const string ApiFileNameDescriptor = "ApiFileName";
            const string ApiClassNameDescriptor = "ApiClassName";

            string basePath = null;
            using (RegistryKey key = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
            {
                using (RegistryKey merkur = key.OpenSubKey(DefaultRegistry))
                {
                    if (merkur != null)
                    {
                        basePath = (string)merkur.GetValue("data", null);
                    }
                }
            }

            if ((basePath == null) || !File.Exists(Path.Combine(basePath, XmlRoot + ".xml")))
            {
                basePath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), DefaultBasePath);
            }

            XmlDocument doc = new XmlDocument();
            doc.Load(Path.Combine(basePath, XmlRoot + ".xml"));
            string filename = doc[XmlRoot][ApiFileNameDescriptor].InnerText.Trim();
            string classname = doc[XmlRoot][ApiClassNameDescriptor].InnerText.Trim();

            if (!File.Exists(filename))
            {
                return (IExplorisInstrumentAccessContainer)Assembly.Load(filename).CreateInstance(classname);
            }
            return (IExplorisInstrumentAccessContainer)Assembly.LoadFrom(filename).CreateInstance(classname);
        }

        public async Task ConnectAsync()
        {
            if (_isConnected)
                return;

            try
            {
                // Initialize instrument access
                await Task.Run(() =>
                {
                    var container = GetApiInstance();
                    container.StartOnlineAccess();
                    _instrumentAccess = container.Get(0);

                    // Get the scans interface
                    _scans = _instrumentAccess.GetMsScanContainer(0);

                    // Subscribe to scan events
                    _scans.MsScanArrived += Scans_ScanArrived;
                });

                _isConnected = true;
                OnConnectionChanged?.Invoke(this, true);
            }
            catch (Exception ex)
            {
                _isConnected = false;
                OnConnectionChanged?.Invoke(this, false);
                throw new Exception("Failed to connect to instrument", ex);
            }
        }

        public async Task DisconnectAsync()
        {
            if (!_isConnected)
                return;

            try
            {
                await Task.Run(() =>
                {
                    if (_scans != null)
                        _scans.MsScanArrived -= Scans_ScanArrived;

                    if (_instrumentAccess != null)
                        (_instrumentAccess as IDisposable)?.Dispose();
                });

                _isConnected = false;
                OnConnectionChanged?.Invoke(this, false);
            }
            catch (Exception ex)
            {
                throw new Exception("Failed to disconnect from instrument", ex);
            }
        }

        private void Scans_ScanArrived(object sender, MsScanEventArgs e)
        {
            OnNewScan?.Invoke(this, e.GetScan());
        }

        public bool IsConnected => _isConnected;
    }
} 