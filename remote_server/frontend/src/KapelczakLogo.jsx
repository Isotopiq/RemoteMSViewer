import React from 'react';

const KapelczakLogo = ({ className = "w-12 h-12", textClassName = "text-2xl" }) => {
  return (
    <div className="flex items-center space-x-3">
      <svg 
        className={className} 
        viewBox="0 0 200 200" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Kapelczak logo - stylized K shape */}
        <path 
          d="M40 40 C40 25 52 13 67 13 L133 13 C148 13 160 25 160 40 L160 67 C160 82 148 94 133 94 L120 94 L160 134 C175 149 175 174 160 189 C145 204 120 204 105 189 L65 149 C50 134 50 109 65 94 L78 81 L40 81 C25 81 13 69 13 54 L13 40 Z" 
          fill="#3B1F5C"
        />
        <path 
          d="M67 40 L133 40 L133 67 L120 67 L160 107 C168 115 168 128 160 136 C152 144 139 144 131 136 L91 96 C83 88 83 75 91 67 L104 54 L67 54 L67 40 Z" 
          fill="#FFFFFF"
        />
        {/* Small circle accent */}
        <circle 
          cx="45" 
          cy="100" 
          r="8" 
          fill="#3B1F5C"
        />
      </svg>
      <span className={`font-bold text-gray-800 ${textClassName}`}>
        Kapelczak
      </span>
    </div>
  );
};

export default KapelczakLogo;