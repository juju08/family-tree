let PEOPLE=[], BY_ID={};
const BRANCH_COLORS = ['Nelly Rivera','Freddy Torres','Glenda Torres','Noemi Torres','Sylvia Diaz','Yolanda Bustos','Jessica Torres'];
function photo(p){return p.photo?`/static/uploads/${p.photo}`:''}
function canEdit(p){ if(window.CURRENT_USER?.is_admin) return true; const uid=window.CURRENT_USER?.id; return p.id===uid || p.spouse_id===uid || p.parent1_id===uid || p.parent2_id===uid; }
function childrenOf(id){return PEOPLE.filter(p=>p.parent1_id===id||p.parent2_id===id).sort((a,b)=>(a.sort_order||999)-(b.sort_order||999)||a.display_name.localeCompare(b.display_name));}
function branchIndex(p, inherited){ if(inherited!==undefined && inherited!==null) return inherited; const i=BRANCH_COLORS.indexOf(p.display_name); return i>=0?i:null; }
function node(p, depth=0, inheritedColor=null){
  const kids=childrenOf(p.id); const color=branchIndex(p,inheritedColor); const div=document.createElement('div'); div.className='branch'+(color!==null?` branch-color-${color}`:'');
  const n=document.createElement('div'); n.className='node'; n.dataset.name=p.display_name.toLowerCase(); n.dataset.depth=depth;
  n.innerHTML=`${kids.length?'<span class="toggle">▾</span>':''}${p.photo?`<img src="${photo(p)}" alt="${p.display_name}">`:`<span class="avatar">${p.display_name.split(' ').map(x=>x[0]).slice(0,2).join('')}</span>`}<span><b>${p.display_name}</b><small>${p.birthday||'Birthday unknown'}</small></span>`;
  n.onclick=(e)=>{ if(e.target.className==='toggle'){div.classList.toggle('collapsed'); e.target.textContent=div.classList.contains('collapsed')?'▸':'▾'; return;} showDetails(p);};
  div.appendChild(n);
  if(kids.length){const c=document.createElement('div'); c.className='children'; kids.forEach(k=>c.appendChild(node(k, depth+1, color))); div.appendChild(c);} return div;
}
function showDetails(p){
  const spouse=p.spouse_id?BY_ID[p.spouse_id]:null; const kids=childrenOf(p.id); const parents=[BY_ID[p.parent1_id],BY_ID[p.parent2_id]].filter(Boolean).map(x=>x.display_name).join(', ');
  document.getElementById('details').innerHTML=`${p.photo?`<img class="detail-photo" src="${photo(p)}" alt="${p.display_name}">`:`<p class="empty-photo">No photo yet</p>`}<h2>${p.display_name}</h2><p><b>Birthday:</b> ${p.birthday||'Unknown'}</p><p><b>Parents:</b> ${parents||'Not listed'}</p><p><b>Spouse:</b> ${spouse?spouse.display_name:'None/Unknown'}</p><p><b>Children:</b> ${kids.length?kids.map(k=>k.display_name).join(', '):'None listed'}</p>${p.notes?`<p><b>Notes:</b> ${p.notes}</p>`:''}${canEdit(p)?`<p><a class="edit" href="/person/${p.id}/edit">Edit / Add Photo</a></p>`:''}`
}
function render(){
  BY_ID=Object.fromEntries(PEOPLE.map(p=>[p.id,p]));
  const roots=PEOPLE.filter(p=>!p.parent1_id&&!p.parent2_id).sort((a,b)=>a.display_name.localeCompare(b.display_name)); const tree=document.getElementById('tree'); tree.innerHTML='<div class="legend"><span class="pill">Click anyone for details</span><span class="pill">Use search to find family</span><span class="pill">Expand/collapse branches</span></div>'; roots.forEach(r=>tree.appendChild(node(r,0,null)));
}
function expandAll(){document.querySelectorAll('.branch').forEach(b=>b.classList.remove('collapsed'));document.querySelectorAll('.toggle').forEach(t=>t.textContent='▾')}
function collapseAll(){document.querySelectorAll('.branch').forEach(b=>{if(b.querySelector('.children'))b.classList.add('collapsed')});document.querySelectorAll('.toggle').forEach(t=>t.textContent='▸')}
document.getElementById('search').addEventListener('input',e=>{const q=e.target.value.toLowerCase();document.querySelectorAll('.node').forEach(n=>{n.style.outline=n.dataset.name.includes(q)&&q?'4px solid #74a7ff':''; if(n.dataset.name.includes(q)&&q){let el=n; while(el){if(el.classList?.contains('branch'))el.classList.remove('collapsed'); el=el.parentElement;}}})});
fetch('/api/tree').then(r=>r.json()).then(d=>{PEOPLE=d;render();});
