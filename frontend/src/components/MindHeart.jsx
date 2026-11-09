// Ilustración del inicio de sesión: el cerebro le da la mano al corazón
export default function MindHeart({ className = '' }) {
  return (
    <svg className={`mind-heart ${className}`} viewBox="0 0 300 330" role="img"
      aria-label="Una persona con un cerebro sonriente en la cabeza que le da la mano a un corazón sonriente en el pecho">
      <path d="M106 176C82 162 70 136 70 104 70 58 106 22 150 22s80 36 80 82c0 32-12 58-36 72v14c56 8 92 42 98 100v40M106 176v14c-56 8-92 42-98 100v40" fill="#FBF6FF" stroke="#4A1858" strokeWidth="4.5" strokeLinecap="round" strokeLinejoin="round" />
      <g className="mh-brain">
        <g fill="#BC96E6"><circle cx="122" cy="82" r="24" /><circle cx="150" cy="66" r="28" /><circle cx="178" cy="82" r="24" /><circle cx="126" cy="108" r="22" /><circle cx="174" cy="108" r="22" /><ellipse cx="150" cy="104" rx="36" ry="28" /></g>
        <path d="M150 46v74" stroke="#A47FD6" strokeWidth="3" strokeLinecap="round" />
        <path d="M134 92c3-3 7-3 10 0M156 92c3-3 7-3 10 0M136 108c8 8 20 8 28 0" stroke="#4A1858" strokeWidth="3.5" fill="none" strokeLinecap="round" />
      </g>
      <g className="mh-hand-top">
        <path d="M150 130v40" stroke="#BC96E6" strokeWidth="10" strokeLinecap="round" />
        <circle cx="150" cy="174" r="8" fill="#BC96E6" />
        <path d="M143 178l-4 8M148 180l-1 9M153 180l1 9M158 178l4 8" stroke="#BC96E6" strokeWidth="4" strokeLinecap="round" />
      </g>
      <g className="mh-hand-bottom">
        <path d="M164 244v-34" stroke="#FFD166" strokeWidth="10" strokeLinecap="round" />
        <circle cx="164" cy="204" r="8" fill="#FFD166" />
        <path d="M157 200l-4-8M162 198l-1-9M167 198l1-9M172 200l4-8" stroke="#FFD166" strokeWidth="4" strokeLinecap="round" />
      </g>
      <g className="mh-heart">
        <path d="M170 316c-36-24-58-46-58-70a26 26 0 0 1 58-14 26 26 0 0 1 58 14c0 24-22 46-58 70z" fill="#FFD166" />
        <path d="M154 258c3-3 7-3 10 0M178 258c3-3 7-3 10 0M158 274c8 7 18 7 26 0" stroke="#4A1858" strokeWidth="3.5" fill="none" strokeLinecap="round" />
      </g>
    </svg>
  )
}
