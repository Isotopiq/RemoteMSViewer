using System;
using System.Windows.Forms;
using System.Windows.Forms.DataVisualization.Charting;
using Thermo.Interfaces.InstrumentAccess_V1;
using Thermo.Interfaces.InstrumentAccess_V1.MsScanContainer;
using Thermo.Interfaces.SpectrumFormat_V1;
using System.Linq;

namespace EddysExploris
{
    public partial class MainForm : Form
    {
        private readonly InstrumentConnection _connection;
        private readonly Chart _chart;
        private readonly TextBox _statusTextBox;
        private readonly Button _connectButton;

        public MainForm()
        {
            InitializeComponent();

            // Initialize connection
            _connection = new InstrumentConnection();
            _connection.OnNewScan += Connection_OnNewScan;
            _connection.OnConnectionChanged += Connection_OnConnectionChanged;

            // Initialize chart
            _chart = new Chart();
            _chart.Dock = DockStyle.Fill;
            _chart.ChartAreas.Add(new ChartArea("MainArea"));
            _chart.Series.Add(new Series("Scan")
            {
                ChartType = SeriesChartType.Line,
                XValueType = ChartValueType.Double,
                YValueType = ChartValueType.Double
            });

            // Initialize status textbox
            _statusTextBox = new TextBox();
            _statusTextBox.Dock = DockStyle.Bottom;
            _statusTextBox.Multiline = true;
            _statusTextBox.Height = 50;
            _statusTextBox.ReadOnly = true;

            // Initialize connect button
            _connectButton = new Button();
            _connectButton.Text = "Connect";
            _connectButton.Dock = DockStyle.Bottom;
            _connectButton.Click += ConnectButton_Click;

            // Add controls to form
            Controls.Add(_chart);
            Controls.Add(_statusTextBox);
            Controls.Add(_connectButton);

            // Set form properties
            Text = "Exploris Live Data";
            Size = new System.Drawing.Size(800, 600);
        }

        private async void ConnectButton_Click(object sender, EventArgs e)
        {
            try
            {
                if (!_connection.IsConnected)
                {
                    _connectButton.Enabled = false;
                    await _connection.ConnectAsync();
                    _connectButton.Text = "Disconnect";
                }
                else
                {
                    _connectButton.Enabled = false;
                    await _connection.DisconnectAsync();
                    _connectButton.Text = "Connect";
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error: {ex.Message}", "Connection Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                _connectButton.Enabled = true;
            }
        }

        private void Connection_OnNewScan(object sender, IMsScan scan)
        {
            if (InvokeRequired)
            {
                Invoke(new Action<object, IMsScan>(Connection_OnNewScan), sender, scan);
                return;
            }

            try
            {
                _chart.Series["Scan"].Points.Clear();
                var centroids = scan.Centroids.ToList();
                foreach (var centroid in centroids)
                {
                    _chart.Series["Scan"].Points.AddXY(centroid.Mz, centroid.Intensity);
                }
            }
            catch (Exception ex)
            {
                _statusTextBox.Text = $"Error updating chart: {ex.Message}";
            }
        }

        private void Connection_OnConnectionChanged(object sender, bool isConnected)
        {
            if (InvokeRequired)
            {
                Invoke(new Action<object, bool>(Connection_OnConnectionChanged), sender, isConnected);
                return;
            }

            _statusTextBox.Text = isConnected ? "Connected to instrument" : "Disconnected from instrument";
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            if (_connection.IsConnected)
            {
                _connection.DisconnectAsync().Wait();
            }
            base.OnFormClosing(e);
        }
    }
} 