/* Render principal y arranque */
function draw(){const a=$('#app');if(!U){a.innerHTML=vLogin();return}
a.innerHTML=`<header class="hd"><h1>Planta · carga y capacidad</h1><nav class="tabs"><button class="${view=='planta'?'on':''}" onclick="view='planta';draw()">Plano</button><button class="${view=='ped'?'on':''}" onclick="view='ped';draw()">Pedidos</button>${adm()?`<button class="${view=='team'?'on':''}" onclick="view='team';draw()">Equipo</button><button class="${view=='flow'?'on':''}" onclick="view='flow';draw()">Flujo</button>`:''}</nav><div class="sp"></div><span>${esc(U.n)} · ${U.r}</span><button class="b" onclick="logout()">Salir</button></header><main>${view=='planta'?vPlanta():view=='ped'?vPed():view=='flow'&&adm()?vFlow():vTeam()}</main>`}

function showError(message){
	const main=$('main');
	if(main)main.insertAdjacentHTML('afterbegin',`<div class="res er" role="alert">${esc(message)}</div>`);
}

async function initApp(){
	if(!authToken){draw();return}
	try{
		const user=await apiFetch('/me');
		U={id:user.id,n:user.full_name,r:user.role,username:user.username};
		await loadAppData();
		draw();
		connectPlantUpdates();
	}catch(e){clearSession();U=null;draw()}
}

initApp();
