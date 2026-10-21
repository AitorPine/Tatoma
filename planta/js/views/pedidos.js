/* Vista Pedidos: órdenes persistidas y evaluación del motor industrial. */
function vPed(){return`<div class="g2"><div class="card tw"><h2>Pedidos</h2><table><tr><th>OF</th><th>Cliente</th><th>Uds</th><th>Entrega</th><th>Estado</th><th>h/ud S·P·M</th><th></th></tr>${S.or.map(order=>`<tr><td>${esc(order.of)}</td><td>${esc(order.cli)}</td><td>${order.q}</td><td>${esc(order.delivery_week||weekKey(order.d))}</td><td>${esc(order.status)}</td><td>${order.hs}·${order.hp}·${order.hm}</td><td>${canPlan()?`<button class="b d" onclick="removeOrder(${order.id})">Quitar</button>`:''}</td></tr>`).join('')}</table></div>
<div class="card"><h2>Evaluar pedido nuevo</h2><div class="fg"><label>OF<input id="fof" value="NUEVO" required></label><label>Cliente<input id="fcli" value="Cliente" required></label><label>Cantidad<input id="fq" type="number" min="1" value="100"></label><label>Semana de entrega<input id="fd" type="number" min="1" max="52" value="20"></label><label>Horas soldadura/ud<input id="fhs" type="number" min="0" step=".05" value="4"></label><label>Horas pintura/ud<input id="fhp" type="number" min="0" step=".05" value=".35"></label><label>Horas montaje/ud<input id="fhm" type="number" min="0" step=".05" value="1.5"></label><label>Plazo previo (semanas)<input id="fl" type="number" min="0" value="2"></label></div><p><button class="b p" onclick="evalo()">Evaluar viabilidad</button></p><div id="res" aria-live="polite"></div></div></div>`}
const fv=key=>+$('#f'+key).value;

function orderPayload(){
	const hours={soldadura:fv('hs'),pintura:fv('hp'),montaje:fv('hm')};
	return{
		code:$('#fof').value.trim(),client:$('#fcli').value.trim(),quantity:fv('q'),
		current_week:weekKey(S.week),delivery_week:weekKey(fv('d')),lead_time_weeks:fv('l'),
		required_skill:'general',hours_per_unit:hours,
		active_phases:Object.keys(hours).filter(area=>hours[area]>0),status:'confirmed'
	};
}

async function evalo(){
	const result=$('#res');
	if(!$('#fof').value.trim()||!$('#fcli').value.trim()||fv('q')<1){result.textContent='Completa el código, el cliente y una cantidad válida.';return}
	const order=orderPayload();
	window._o=order;
	result.textContent='Calculando capacidad y alternativas…';
	try{
		const evaluation=await apiFetch('/simulations/evaluate',{method:'POST',body:order});
		window._evaluation=evaluation;
		const conflicts=evaluation.conflicts.map(conflict=>`<li>${esc(conflict.week)} · ${esc(conflict.area)}: ${esc(conflict.message)}</li>`).join('');
		const suggestions=evaluation.suggestions.filter(item=>item.viable).map((item,index)=>`<li><b>${esc(item.title)}</b>: ${esc(item.description)} ${canPlan()?`<button class="b" onclick="applyStrategy(${index})">Aplicar</button>`:''}</li>`).join('');
		const status=evaluation.viable
			?`<div class="res ok"><b>Viable.</b> ${canPlan()?'<button class="b p" onclick="acc()">Aceptar pedido</button>':''}</div>`
			:`<div class="res er"><b>No es viable.</b><ul>${conflicts}</ul><b>Alternativas viables del motor</b><ul>${suggestions||'<li>No se encontró una alternativa automática viable.</li>'}</ul><p>${esc(evaluation.ai_advisor.summary)}</p><small>${esc(evaluation.ai_advisor.generated_by)} · Riesgo ${esc(evaluation.ai_advisor.risk_level)}</small></div>`;
		result.innerHTML=status;
	}catch(e){result.textContent=e.message}
}

async function acc(){
	try{
		await apiFetch('/orders',{method:'POST',body:window._o});
		await loadAppData();draw();
	}catch(e){showError(e.message)}
}

async function applyStrategy(index){
	const strategy=window._evaluation?.suggestions.filter(item=>item.viable)[index];
	if(!strategy)return;
	try{
		await apiFetch('/simulations/apply',{method:'POST',body:{
			order:window._o,selected_strategy_code:strategy.strategy_code,allocations:strategy.allocations,
			capacity_adjustments_to_create:strategy.capacity_adjustments_to_create,
			final_delivery_week:strategy.proposed_delivery_week
		}});
		await loadAppData();draw();
	}catch(e){showError(e.message)}
}

async function removeOrder(id){
	try{await apiFetch(`/orders/${id}`,{method:'DELETE'});await loadAppData();draw()}
	catch(e){showError(e.message)}
}
