/* Autenticación y control de permisos */
const adm=()=>U&&U.r==='admin';
const canPlan=()=>U&&U.r!=='viewer';
const vLogin=()=>`<div class="login"><h1>Planta</h1><div class="card"><label>Usuario<input id="lu" autocomplete="username"></label><label>Contraseña<input id="lp" type="password" autocomplete="current-password" onkeydown="event.key=='Enter'&&login()"></label><button class="b p" onclick="login()">Entrar</button><span id="le" style="color:var(--er)"></span><small style="color:var(--mut)">Introduce las credenciales asignadas por el administrador.</small></div></div>`;
async function login(){
	const error=$('#le');
	try{
		const result=await apiFetch('/auth/login',{method:'POST',authenticated:false,body:{username:$('#lu').value.trim(),password:$('#lp').value}});
		setSession(result.access_token,result.refresh_token);
		U={id:result.user.id,n:result.user.full_name,r:result.user.role,username:result.user.username};
		await loadAppData();
		draw();
		connectPlantUpdates();
	}catch(e){if(error)error.textContent=e.message}
}

async function logout(){
	try{await apiFetch('/auth/logout',{method:'POST'})}catch(e){}
	disconnectPlantUpdates();
	clearSession();
	U=null;
	draw();
}
