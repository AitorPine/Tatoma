/* Constantes y utilidades generales */
const API_BASE=(window.TATOMA_API_URL||'/api/v1').replace(/\/+$/,'');
const AR=['soldadura','pintura','montaje'],AC={soldadura:'--so',pintura:'--pi',montaje:'--mo'},SL={act:'Activa',parada:'Parada',mant:'En mantenimiento'};
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const $=s=>document.querySelector(s),col=i=>`hsl(${(i*57+20)%360} 48% 52%)`;
