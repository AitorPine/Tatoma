let authToken=sessionStorage.getItem('tatoma_token');
let refreshToken=sessionStorage.getItem('tatoma_refresh_token');

async function apiFetch(path,{method='GET',body,headers={},authenticated=true}={}){
  const send=async token=>{
    const requestHeaders={...headers};
    if(body!==undefined&&!(body instanceof FormData))requestHeaders['Content-Type']='application/json';
    if(authenticated&&token)requestHeaders.Authorization=`Bearer ${token}`;
    return fetch(`${API_BASE}${path}`,{
      method,headers:requestHeaders,
      body:body===undefined?undefined:body instanceof FormData?body:JSON.stringify(body)
    });
  };
  let response=await send(authToken);
  if(response.status===401&&authenticated&&refreshToken){
    const renewed=await fetch(`${API_BASE}/auth/refresh`,{method:'POST',headers:{Authorization:`Bearer ${refreshToken}`}});
    if(renewed.ok){
      const tokens=await renewed.json();
      setSession(tokens.access_token,tokens.refresh_token);
      response=await send(authToken);
    }
  }
  const data=response.status===204?null:await response.json().catch(()=>null);
  if(!response.ok){
    if(response.status===401&&authenticated)clearSession();
    throw new Error(data?.detail||`Error ${response.status} al comunicarse con el servidor.`);
  }
  return data;
}

function setSession(token,refresh){
  authToken=token;
  refreshToken=refresh||null;
  sessionStorage.setItem('tatoma_token',token);
  if(refreshToken)sessionStorage.setItem('tatoma_refresh_token',refreshToken);
}

function clearSession(){
  authToken=null;
  refreshToken=null;
  sessionStorage.removeItem('tatoma_token');
  sessionStorage.removeItem('tatoma_refresh_token');
}