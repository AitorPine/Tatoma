/* Vista Flujo: secuencia y desplazamiento semanal de las fases. */
function vFlow(){const areaOptions=AR.map(area=>[area,area]);return`<div class="card tw"><h2>Flujo de trabajo</h2><p class="lg">Cada fase se programa el número indicado de semanas antes de la entrega. El tiempo de producción por unidad se define en cada pedido.</p><table><tr><th>Orden</th><th>Fase</th><th>Área</th><th>Semanas antes de entrega</th><th>Opcional</th><th></th></tr>${S.flow.map((step,index)=>`<tr><td><button class="b" onclick="mvFl(${index},-1)" aria-label="Subir">▲</button> <button class="b" onclick="mvFl(${index},1)" aria-label="Bajar">▼</button></td><td><input value="${esc(step.n)}" onchange="fl(${index},'n',this.value)"></td><td><select onchange="fl(${index},'a',this.value)">${areaOptions.map(([value,label])=>`<option value="${value}" ${value===step.a?'selected':''}>${label}</option>`).join('')}</select></td><td><input type="number" min="0" max="52" value="${step.offset_weeks_before_delivery??step.f??0}" onchange="fl(${index},'offset',+this.value)"></td><td><input type="checkbox" ${step.is_optional?'checked':''} onchange="fl(${index},'optional',this.checked)"></td><td><button class="b d" onclick="delFl(${index})">Quitar</button></td></tr>`).join('')}</table><p><button class="b p" onclick="addFl()">Añadir fase</button> <button class="b" onclick="restoreFlow()">Restaurar flujo inicial</button></p></div>`}

async function saveWorkflow(){
	const steps=S.flow.map((step,index)=>({
		step_order:index+1,area_id:step.a,name:step.n,
		offset_weeks_before_delivery:Number(step.offset_weeks_before_delivery??step.f??0),
		is_optional:Boolean(step.is_optional)
	}));
	try{await apiFetch('/workflow',{method:'PUT',body:steps});await loadAppData();draw()}
	catch(e){showError(e.message)}
}

function fl(index,key,value){
	const step=S.flow[index];
	if(key==='offset'){step.offset_weeks_before_delivery=value;step.f=value;step.t=value}
	else if(key==='optional')step.is_optional=value;
	else step[key]=value;
	saveWorkflow();
}

function mvFl(index,direction){
	const target=index+direction;
	if(target<0||target>=S.flow.length)return;
	[S.flow[index],S.flow[target]]=[S.flow[target],S.flow[index]];
	saveWorkflow();
}

function addFl(){S.flow.push({n:'Fase nueva',a:'montaje',f:0,t:0,offset_weeks_before_delivery:0,is_optional:false});saveWorkflow()}
function delFl(index){S.flow.splice(index,1);saveWorkflow()}
function restoreFlow(){S.flow=DEF();saveWorkflow()}
