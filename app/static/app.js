const state = { view: 'overview', reviewId: null, role: 'Creator', dashboard: null };
const API = '/api';
const page = document.getElementById('pageContent');

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function initials(role) { return ({Creator:'CR',Manager:'MG',Reviewer:'RV',Admin:'AD'})[role] || 'DU'; }
function actorName(role=state.role) { return `Demo ${role.toLowerCase()}`; }
function titleFor(view) { return ({overview:'Overview','new-review':'Review draft',claims:'Claims ledger',rules:'Rule library',insights:'Insights & audit','review-detail':'Review details'})[view] || 'Overview'; }
function dateTime(value) {
  if (!value) return '—';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
}
function dateShort(value) {
  if (!value) return '—';
  const d = new Date(`${value}T00:00:00`);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString([], {month:'short',day:'numeric',year:'numeric'});
}
function statusLabel(value) {
  return ({needs_review:'Needs review',approved:'Approved',disputed:'Disputed',changes_requested:'Changes requested',open:'Open',accepted:'Accepted',expired:'Expired',pending:'Pending'})[value] || (value || 'Unknown').replaceAll('_',' ');
}
function statusPill(value) {
  const safe = esc(value || 'unknown');
  return `<span class="status status-${safe}">${esc(statusLabel(value))}</span>`;
}
function toast(message, type='success') {
  const region = document.getElementById('toastRegion');
  const el = document.createElement('div');
  el.className = `toast ${type}`; el.textContent = message; region.appendChild(el);
  setTimeout(() => { el.style.opacity='0'; el.style.transform='translateY(6px)'; setTimeout(()=>el.remove(),220); }, 3200);
}
async function request(path, options={}) {
  let response;
  try {
    response = await fetch(`${API}${path}`, {headers:{'Content-Type':'application/json', ...(options.headers||{})}, ...options});
  } catch (e) {
    throw new Error('Could not reach the local BrandLens API. Is the server running?');
  }
  const body = await response.json().catch(()=>({detail:'Unexpected server response.'}));
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : `Request failed (${response.status}).`);
  return body;
}
function navTo(view, reviewId=null) {
  state.view=view; state.reviewId=reviewId;
  document.getElementById('currentPageName').textContent=titleFor(view);
  document.querySelectorAll('.nav-item').forEach(btn=>btn.classList.toggle('active', btn.dataset.view===view || (view==='review-detail' && btn.dataset.view==='overview')));
  document.getElementById('sidebar').classList.remove('open');
  renderCurrent();
}
function pageHead(eyebrow,title,subtitle,actions='') {
  return `<div class="page-head"><div><div class="eyebrow">${esc(eyebrow)}</div><h1 class="page-title">${esc(title)}</h1><p class="page-subtitle">${esc(subtitle)}</p></div>${actions ? `<div class="page-head-actions">${actions}</div>`:''}</div>`;
}
function metricCard(label,value,foot,icon) {
  return `<div class="metric-card"><div class="metric-top"><span>${esc(label)}</span><span class="metric-icon">${icon}</span></div><div class="metric-number">${esc(value)}</div><div class="metric-foot">${foot}</div></div>`;
}
function reviewRow(review) {
  const count = review.findings.filter(f=>['open','disputed'].includes(f.status)).length;
  return `<div class="review-row" role="button" tabindex="0" data-open-review="${esc(review.id)}"><div class="doc-icon">▤</div><div class="review-row-main"><b>${esc(review.title)}</b><small>${esc(review.channel)} · ${esc(review.id)} · v${review.current_version}</small></div><div class="review-row-end">${statusPill(review.status)}<span class="finding-count">${count} open finding${count===1?'':'s'}</span></div></div>`;
}
async function renderCurrent() {
  page.innerHTML = '<div class="loading-state"><div class="loader"></div><p>Loading workspace…</p></div>';
  try {
    if(state.view==='overview') await renderOverview();
    else if(state.view==='new-review') renderNewReview();
    else if(state.view==='claims') await renderClaims();
    else if(state.view==='rules') await renderRules();
    else if(state.view==='insights') await renderInsights();
    else if(state.view==='review-detail') await renderReviewDetail(state.reviewId);
  } catch (error) {
    page.innerHTML = `<div class="panel"><div class="panel-body"><div class="callout"><span class="callout-icon">!</span><div><strong>Unable to load this view</strong><br>${esc(error.message)}</div></div><button class="btn btn-secondary" id="retryView" style="margin-top:16px">Try again</button></div></div>`;
    document.getElementById('retryView')?.addEventListener('click', renderCurrent);
  }
}
async function renderOverview() {
  const data = await request('/dashboard'); state.dashboard=data;
  page.innerHTML = `${pageHead('WORKSPACE OVERVIEW','Brand review, without the guesswork.','Keep claims, language and approval decisions connected to the sources that support them.', '<button class="btn btn-primary" id="startReview"><span class="btn-icon">＋</span> Start a review</button>')}
    <div class="demo-banner"><strong>Demo workspace.</strong> Brand facts, claim evidence and all names here are fictional seed data. Findings demonstrate the workflow; they are not legal advice or proof of production accuracy.</div>
    <div class="metrics-grid">
      ${metricCard('Total reviews',data.reviews,'Across this local demo','▤')}
      ${metricCard('Awaiting decision',data.pending,`${data.approved} approved in the demo`,'◷')}
      ${metricCard('Open findings',data.open_findings,'Current review versions only','⌁')}
      ${metricCard('Approved reviews',data.approved,'Human decision recorded','✓')}
    </div>
    <div class="content-grid">
      <section class="panel"><div class="panel-head"><div><h2>Recent reviews</h2><p>Drafts and decisions from the local workspace</p></div><button class="text-link" id="viewAllReviews">View latest</button></div><div class="panel-body"><div class="review-list">${data.recent.length ? data.recent.map(reviewRow).join('') : '<div class="empty-state"><strong>No reviews yet</strong>Start your first draft review to create a record.</div>'}</div></div></section>
      <div>
        <section class="panel quick-start"><div class="panel-body"><div class="quick-kicker">Your review workspace</div><h2>Confidence starts with evidence.</h2><p>Catch missing approvals and outdated claims before a draft goes live. Keep people in control of every decision.</p><button class="btn" id="quickReview">Review a draft <span>→</span></button><div class="checklist"><div class="check-row"><i>✓</i><span>Rule-linked findings with a proposed fix</span></div><div class="check-row"><i>✓</i><span>Versioned claims with validity dates</span></div><div class="check-row"><i>✓</i><span>Disputes and approval decisions in an audit trail</span></div></div></div></section>
        <div class="section-label">ROUND 2 FOCUS</div>
        <section class="panel"><div class="panel-body"><div class="rule-card-top"><strong style="font:700 12px Manrope;color:#284652">Three improvements</strong><span class="tag">MVP scope</span></div><div class="checklist" style="gap:14px;margin-top:15px"><div style="display:flex;gap:9px"><span class="callout-icon">1</span><div><b style="font-size:10px">Evidence-linked claims</b><div class="small-muted">Match claim text to current, scoped records.</div></div></div><div style="display:flex;gap:9px"><span class="callout-icon">2</span><div><b style="font-size:10px">Citation-or-silence</b><div class="small-muted">Each flag shows its rule or claim source.</div></div></div><div style="display:flex;gap:9px"><span class="callout-icon">3</span><div><b style="font-size:10px">Human review + gap signals</b><div class="small-muted">Creators can dispute; reviewers decide.</div></div></div></div></div></section>
      </div>
    </div>`;
  document.getElementById('startReview').onclick=()=>navTo('new-review');
  document.getElementById('quickReview').onclick=()=>navTo('new-review');
  document.getElementById('viewAllReviews').onclick=async()=>{
    const reviews=await request('/reviews');
    page.innerHTML=`${pageHead('WORKSPACE','All reviews','Open a review to inspect the current draft, linked findings and recorded decisions.','<button class="btn btn-primary" id="startReview2">＋ Start a review</button>')}<section class="panel"><div class="panel-body"><div class="review-list">${reviews.map(reviewRow).join('')||'<div class="empty-state">No reviews yet.</div>'}</div></div></section>`;
    document.getElementById('startReview2').onclick=()=>navTo('new-review'); bindReviewRows();
  };
  bindReviewRows();
}
function renderNewReview() {
  const sample = "India's No.1 skincare brand, with guaranteed results in one day. Our serum is 40% more effective than leading brands!!!";
  page.innerHTML = `${pageHead('CONTENT REVIEW','Review a draft before it goes live.','Run the current deterministic checks against the fictional brand rules and approved-claims ledger.')}
    <div class="callout" style="margin-bottom:18px"><span class="callout-icon">i</span><div><strong>Source-grounded by design.</strong> The demo checks terminology, superlatives, absolute promises, expired claims and a small tone heuristic. It does not call an external AI model, and it does not decide legal compliance.</div></div>
    <div class="panel"><div class="panel-head"><div><h2>New review</h2><p>Submit a social post, email or web copy draft.</p></div><span class="tag">Step 1 of 3 · Submit</span></div><div class="panel-body"><form id="newReviewForm">
      <div class="form-grid"><div class="field"><label for="reviewTitle">Review title</label><input id="reviewTitle" maxlength="120" value="Launch campaign draft" required /></div><div class="field"><label for="reviewChannel">Intended channel</label><select id="reviewChannel"><option>Instagram / Social</option><option>LinkedIn post</option><option>Website / Landing page</option><option>Email campaign</option><option>Blog / Article</option><option>Presentation</option></select></div></div>
      <div class="field" style="max-width:520px"><label for="reviewProduct">Product / claim scope</label><select id="reviewProduct"><option>LumaSkin Serum</option><option>LumaSkin Hydration Gel</option><option>Not specified</option></select><small>Scope is checked when draft text matches an approved claim record.</small></div>
      <div class="field"><label for="draftInput">Draft content</label><textarea id="draftInput" rows="9" minlength="5" maxlength="20000" required>${esc(sample)}</textarea><small>Tip: keep at least one claim without approval, one expired claim, or one terminology issue to see findings in the demo.</small></div>
      <div class="form-actions"><button class="btn btn-primary" type="submit">Run checks & create review <span>→</span></button><button class="btn btn-secondary" type="button" id="clearDraft">Clear draft</button><button class="btn btn-quiet" type="button" id="loadSample">Load demo example</button></div>
    </form></div></div>
    <div class="section-label">WHAT HAPPENS NEXT</div><div class="insight-stats"><div class="insight-stat"><b>01</b><span>Exact rules run first</span></div><div class="insight-stat"><b>02</b><span>Findings link to sources</span></div><div class="insight-stat"><b>03</b><span>People decide what ships</span></div></div>`;
  document.getElementById('clearDraft').onclick=()=>document.getElementById('draftInput').value='';
  document.getElementById('loadSample').onclick=()=>document.getElementById('draftInput').value=sample;
  document.getElementById('newReviewForm').onsubmit=async e=>{
    e.preventDefault();
    const draft_text=document.getElementById('draftInput').value.trim();
    if(draft_text.length<5){toast('Please enter at least 5 characters.','error');return;}
    try{
      const review=await request('/reviews',{method:'POST',body:JSON.stringify({title:document.getElementById('reviewTitle').value.trim()||'Untitled review',channel:document.getElementById('reviewChannel').value,product_scope:document.getElementById('reviewProduct').value,draft_text,created_by:actorName(),actor_role:state.role})});
      toast(`Review created with ${review.findings.length} finding(s).`);
      navTo('review-detail',review.id);
    }catch(error){toast(error.message,'error');}
  };
}
async function renderReviewDetail(reviewId) {
  const review=await request(`/reviews/${encodeURIComponent(reviewId)}`);
  const audit=await request(`/reviews/${encodeURIComponent(reviewId)}/audit`);
  const canCreate=['Creator','Admin'].includes(state.role), canApprove=['Manager','Reviewer','Admin'].includes(state.role);
  const open=review.findings.filter(f=>['open','disputed'].includes(f.status)).length;
  const findingCards=review.findings.length ? review.findings.map(f=>`
    <article class="finding-card ${esc(f.severity)}"><div class="finding-top"><div><h3 class="finding-title">${esc(f.title)}</h3><div class="finding-meta"><span class="severity ${esc(f.severity)}">${esc(f.severity)} priority</span><span class="tag">${esc(f.category)}</span></div></div>${statusPill(f.status)}</div>
      <div class="finding-excerpt">“${esc(f.excerpt)}”</div><p class="finding-explanation">${esc(f.explanation)}</p><div class="source-box"><span class="source-mark">↗</span><div class="source-copy"><small>Source / rule cited</small><b>${esc(f.source_label)}</b></div></div>
      <div class="suggestion"><strong>Suggested next step:</strong> ${esc(f.suggestion)}</div>
      ${f.status==='disputed' && f.dispute_reason ? `<div class="callout" style="margin-bottom:10px;background:#fff7e9;border-color:#f1e2c0;color:#8b691f"><span class="callout-icon">?</span><div><strong>Creator dispute:</strong> ${esc(f.dispute_reason)}</div></div>`:''}
      ${['open','disputed'].includes(f.status) && canCreate ? `<div class="finding-actions"><button class="btn btn-secondary btn-small" data-accept-finding="${esc(f.id)}">✓ Accept suggestion</button><button class="btn btn-quiet btn-small" data-dispute-finding="${esc(f.id)}">Dispute finding</button></div>`:''}
      ${!['open','disputed'].includes(f.status) ? `<div class="finding-state">${f.status==='accepted'?'Suggestion acknowledged; draft was not changed automatically.':'Finding status: '+esc(statusLabel(f.status))}</div>`:''}
    </article>`).join('') : '<div class="empty-state"><strong>No findings from the current checks.</strong>This means the deterministic checks did not find a supported issue; it is not a compliance guarantee.</div>';
  const auditMarkup=audit.length ? audit.map(ev=>`<div class="timeline-event"><div class="timeline-dot"></div><div class="timeline-copy"><b>${esc(ev.event_type.replaceAll('_',' '))} · ${esc(ev.actor_role)}</b><p>${esc(ev.detail)}</p><small>${esc(ev.actor)} · ${dateTime(ev.created_at)} · v${esc(ev.version_no??'—')}</small></div></div>`).join('') : '<div class="empty-inline">No audit events yet.</div>';
  page.innerHTML = `${pageHead('REVIEW WORKFLOW',review.title,`${review.channel} · ${review.id} · version ${review.current_version}`, `<button class="btn btn-secondary" id="backOverview">← Back</button>`)}
    <div class="status-line" style="margin:-8px 0 19px">${statusPill(review.status)}<span class="tag">${open} open / disputed</span><span class="tag">${review.findings.length} finding${review.findings.length===1?'':'s'} in v${review.current_version}</span></div>
    <div class="review-layout">
      <section><div class="panel"><div class="panel-head"><div><h2>Draft content</h2><p>Review version ${review.current_version} · ${esc(review.created_by)}</p></div><span class="tag">${canCreate?'Editable':'Read only for this role'}</span></div><div class="panel-body"><textarea class="draft-editor" id="editDraft" ${canCreate?'':'readonly'}>${esc(review.draft_text)}</textarea><div class="editor-foot"><span>Saving creates a new version and reruns checks.</span><span id="charCount">${review.draft_text.length} chars</span></div><div class="form-actions" style="margin-top:14px"><button class="btn btn-primary" id="saveRevision" ${canCreate?'':'disabled'}>Save revision & rescan</button><button class="btn btn-secondary" id="copyDraft">Copy draft</button></div><div class="divider"></div><div class="review-pane-header"><h2>Human approval</h2><span>Role: ${esc(state.role)}</span></div><p class="small-muted">No content is published or automatically approved. The role selector demonstrates the workflow; it is not authentication.</p><div class="form-actions" style="margin-top:12px">${canApprove?`<button class="btn btn-primary" id="approveReview">Approve review</button><button class="btn btn-secondary" id="requestChanges">Request changes</button>`:`<button class="btn btn-quiet" disabled>Approval controls require Manager / Reviewer</button>`}</div></div></div>
        <section class="panel" style="margin-top:17px"><div class="panel-head"><div><h2>Version history & audit trail</h2><p>Recorded actions for this review</p></div><span class="tag">${audit.length} events</span></div><div class="panel-body"><div class="timeline">${auditMarkup}</div></div></section>
      </section>
      <section><div class="review-pane-header"><h2>Checks & findings</h2><span>Rules + claims ledger</span></div><div class="findings-list">${findingCards}</div><div class="callout" style="margin-top:13px"><span class="callout-icon">i</span><div><strong>Citation-or-silence.</strong> An actionable finding must name a stored rule or claims record. The current MVP uses deterministic checks only; the tone heuristic is advisory.</div></div></section>
    </div>`;
  document.getElementById('backOverview').onclick=()=>navTo('overview');
  document.getElementById('editDraft').addEventListener('input',e=>document.getElementById('charCount').textContent=`${e.target.value.length} chars`);
  document.getElementById('saveRevision').onclick=async()=>{
    try{const updated=await request(`/reviews/${encodeURIComponent(review.id)}/actions`,{method:'POST',body:JSON.stringify({action:'edit',actor:actorName(),actor_role:state.role,draft_text:document.getElementById('editDraft').value})});toast(`Saved version ${updated.current_version}; checks rerun.`);await renderReviewDetail(review.id);}catch(error){toast(error.message,'error');}
  };
  document.getElementById('copyDraft').onclick=()=>{
    const txt=document.getElementById('editDraft').value;
    if(navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(()=>toast('Draft copied.')).catch(()=>fallbackCopy(txt)); else fallbackCopy(txt);
  };
  document.querySelectorAll('[data-accept-finding]').forEach(btn=>btn.onclick=()=>runFindingAction('accept',btn.dataset.acceptFinding));
  document.querySelectorAll('[data-dispute-finding]').forEach(btn=>btn.onclick=()=>runFindingAction('dispute',btn.dataset.disputeFinding));
  document.getElementById('approveReview')?.addEventListener('click',async()=>{
    const hasOpen=review.findings.some(f=>['open','disputed'].includes(f.status));
    let reason='';
    if(hasOpen){reason=window.prompt('Open or disputed findings remain. Enter the reviewer rationale for overriding them, or Cancel:','Reviewed manually; proceeding with documented human decision.');if(reason===null)return;if(!reason.trim()){toast('A rationale is required while findings remain open.','error');return;}}
    try{await request(`/reviews/${encodeURIComponent(review.id)}/actions`,{method:'POST',body:JSON.stringify({action:'approve',actor:actorName(),actor_role:state.role,reason})});toast('Human approval recorded.');await renderReviewDetail(review.id);}catch(error){toast(error.message,'error');}
  });
  document.getElementById('requestChanges')?.addEventListener('click',async()=>{
    const reason=window.prompt('What should the creator address?','Please update the evidence for the comparative claim and simplify the tone.');if(reason===null)return;
    try{await request(`/reviews/${encodeURIComponent(review.id)}/actions`,{method:'POST',body:JSON.stringify({action:'request_changes',actor:actorName(),actor_role:state.role,reason})});toast('Changes requested and audit event recorded.');await renderReviewDetail(review.id);}catch(error){toast(error.message,'error');}
  });
  async function runFindingAction(action,findingId){
    let reason='';if(action==='dispute'){reason=window.prompt('Why do you disagree with this finding?','The wording is intentional; please review the product context.');if(reason===null)return;if(!reason.trim()){toast('Please enter a dispute reason.','error');return;}}
    try{await request(`/reviews/${encodeURIComponent(review.id)}/actions`,{method:'POST',body:JSON.stringify({action,actor:actorName(),actor_role:state.role,finding_id:findingId,reason})});toast(action==='accept'?'Suggestion acknowledged; draft unchanged.':'Dispute recorded for human review.');await renderReviewDetail(review.id);}catch(error){toast(error.message,'error');}
  }
}
function fallbackCopy(text){const el=document.createElement('textarea');el.value=text;document.body.appendChild(el);el.select();try{document.execCommand('copy');toast('Draft copied.');}catch{toast('Copy was not available in this browser.','error');}el.remove();}
function bindReviewRows(){document.querySelectorAll('[data-open-review]').forEach(row=>{const go=()=>navTo('review-detail',row.dataset.openReview);row.addEventListener('click',go);row.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go();}});});}
async function renderClaims(){
  const claims=await request('/claims');
  const rows=claims.map(c=>`<tr><td><strong>${esc(c.id)} · ${esc(c.claim)}</strong><small>${esc(c.note)}</small></td><td>${esc(c.product_scope)}<small>${esc(c.channel_scope)}</small></td><td>${esc(c.valid_from)}<small>to ${esc(c.valid_until)}</small></td><td>${statusPill(c.is_current?'approved':c.status)}</td><td>${esc(c.approver)}<small>${esc(c.evidence_source)}</small></td></tr>`).join('');
  page.innerHTML=`${pageHead('SOURCE LIBRARY','Approved-claims ledger','Keep approved statements tied to product scope, channel, evidence owner and validity dates. This demo ledger contains fictional records.')}
    <div class="demo-banner"><strong>Important:</strong> CL-001 to CL-003 are fictional seed records for testing. Their evidence labels are not public sources. A claim marked expired is stale approval—not proof that the underlying statement is false.</div>
    <div class="claim-grid"><section class="panel"><div class="panel-head"><div><h2>Claims & facts</h2><p>${claims.length} claim records · current and expired statuses</p></div><span class="tag">Versioned ledger demo</span></div><div class="table-wrap"><table class="data-table"><thead><tr><th>Approved statement</th><th>Scope</th><th>Validity</th><th>Status</th><th>Evidence / owner</th></tr></thead><tbody>${rows}</tbody></table></div></section>
    <section class="panel claim-add-panel"><div class="panel-head"><div><h2>Add a claim record</h2><p>Creates a local ledger record for this demo</p></div></div><div class="panel-body"><form id="claimForm"><div class="field"><label for="claimText">Approved statement</label><textarea id="claimText" rows="3" required placeholder="Exact approved claim wording"></textarea></div><div class="field"><label for="claimProduct">Product / scope</label><input id="claimProduct" required placeholder="e.g. LumaSkin Hydration Gel" /></div><div class="field"><label for="claimChannel">Channel scope</label><input id="claimChannel" value="All channels" required /></div><div class="field"><label for="claimEvidence">Evidence reference</label><input id="claimEvidence" required placeholder="Internal memo ID / source reference" /><small>Use a source you are authorised to store. Avoid confidential details in this demo.</small></div><div class="field"><label for="claimApprover">Approver</label><input id="claimApprover" value="Demo reviewer" required /></div><div class="form-grid"><div class="field"><label for="claimFrom">Valid from</label><input id="claimFrom" type="date" value="${new Date().toISOString().slice(0,10)}" required /></div><div class="field"><label for="claimUntil">Valid until</label><input id="claimUntil" type="date" value="2027-12-31" required /></div></div><div class="field"><label for="claimNote">Scope note (optional)</label><input id="claimNote" placeholder="Limitations or conditions" /></div><button class="btn btn-primary" type="submit" ${state.role==='Admin'?'':'disabled'}>＋ Save claim record</button>${state.role==='Admin'?'':'<p class="small-muted">Switch to the Admin demo role to add an approved claim record.</p>'}</form></div></section></div>`;
  document.getElementById('claimForm').onsubmit=async e=>{
    e.preventDefault();const payload={claim:document.getElementById('claimText').value,product_scope:document.getElementById('claimProduct').value,channel_scope:document.getElementById('claimChannel').value,evidence_source:document.getElementById('claimEvidence').value,approver:document.getElementById('claimApprover').value,valid_from:document.getElementById('claimFrom').value,valid_until:document.getElementById('claimUntil').value,note:document.getElementById('claimNote').value,actor_role:state.role};
    try{await request('/claims',{method:'POST',body:JSON.stringify(payload)});toast('Claim record saved to local ledger.');await renderClaims();}catch(error){toast(error.message,'error');}
  };
}
async function renderRules(){
  const rules=await request('/rules');
  page.innerHTML=`${pageHead('GOVERNANCE LIBRARY','Rules with an owner and a source.','This demo encodes a small fictional style guide. Each finding references a rule ID or a specific claim record.')}
    <div class="callout" style="margin-bottom:18px"><span class="callout-icon">i</span><div><strong>Rule types are intentionally limited.</strong> Exact terms and evidence status are deterministic. Tone checks are advisory. This is not a legal review of ASCI or CCPA rules.</div></div>
    <div class="rule-list">${rules.map(r=>`<article class="rule-card"><div class="rule-card-top"><span class="rule-id">${esc(r.id)}</span><span class="rule-category">${esc(r.category)}</span></div><h3>${esc(r.title)}</h3><p>${esc(r.rule_text)}</p><div class="rule-card-foot"><span>${esc(r.source_name)} · ${esc(r.version)}</span>${statusPill(r.status==='active'?'approved':r.status)}</div></article>`).join('')}</div>`;
}
async function renderInsights(){
  const data=await request('/insights');
  const max=Math.max(1,...data.rule_clusters.map(x=>x.count));
  const bars=data.rule_clusters.map(x=>`<div class="bar-row"><span class="bar-label">${esc(x.source_id)} · ${esc(x.title)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(4,100*x.count/max)}%"></div></div><span class="bar-count">${x.count}</span></div>`).join('')||'<div class="empty-inline">No findings in the current versions yet.</div>';
  const disputes=data.disputes.map(d=>`<div class="dispute-item"><b>${esc(d.title)} · ${esc(d.source_id)}</b><p>${esc(d.dispute_reason)}</p><small>${esc(d.review_title)} · ${dateTime(d.created_at)}</small></div>`).join('')||'<div class="empty-inline">No disputed findings yet. Disputed rules will appear here as possible guideline-gap signals.</div>';
  const audit=data.audit.map(ev=>`<div class="timeline-event"><div class="timeline-dot"></div><div class="timeline-copy"><b>${esc(ev.event_type.replaceAll('_',' '))} · ${esc(ev.actor_role)}</b><p>${esc(ev.detail)}</p><small>${esc(ev.actor)} · ${dateTime(ev.created_at)} · ${esc(ev.review_id||'workspace')}</small></div></div>`).join('')||'<div class="empty-inline">No activity recorded yet.</div>';
  page.innerHTML=`${pageHead('GOVERNANCE INSIGHTS','Learn from repeated review friction.','A lightweight view of current findings and disputed rules. Counts are software-generated from the local demo database, not user research.')}
    <div class="insight-stats"><div class="insight-stat"><b>${data.findings_total}</b><span>Findings in current versions</span></div><div class="insight-stat"><b>${data.rule_clusters.reduce((s,x)=>s+x.disputed,0)}</b><span>Current disputed findings</span></div><div class="insight-stat"><b>${new Set(data.rule_clusters.map(x=>x.source_id)).size}</b><span>Source/rule groups seen</span></div></div>
    <div class="content-grid"><section class="panel"><div class="panel-head"><div><h2>Finding clusters by source</h2><p>Repeated patterns can inform human-approved rule updates.</p></div></div><div class="panel-body"><div class="bar-list">${bars}</div><div class="divider"></div><div class="small-muted">This prototype counts rule-linked findings. It does not use semantic clustering or claim statistical significance.</div></div></section>
    <div><section class="panel"><div class="panel-head"><div><h2>Disputes as gap signals</h2><p>Human review is required before changing a guideline.</p></div></div><div class="panel-body">${disputes}</div></section><section class="panel" style="margin-top:17px"><div class="panel-head"><div><h2>Recent audit events</h2><p>Submitted drafts, revisions and decisions</p></div></div><div class="panel-body"><div class="timeline">${audit}</div></div></section></div></div>`;
}

document.querySelectorAll('.nav-item').forEach(btn=>btn.addEventListener('click',()=>navTo(btn.dataset.view)));
document.getElementById('roleSelect').addEventListener('change',e=>{
  state.role=e.target.value;document.getElementById('roleAvatar').textContent=initials(state.role);toast(`Demo role switched to ${state.role}. This is not authentication.`,'success');
  if(['review-detail','claims','new-review'].includes(state.view)) renderCurrent();
});
document.getElementById('mobileMenu').addEventListener('click',()=>document.getElementById('sidebar').classList.toggle('open'));
document.getElementById('resetDemo').addEventListener('click',async()=>{
  if(!window.confirm('Reset local demo data to the fictional seed records? Your locally created reviews and claims will be removed.'))return;
  try{await request('/demo/reset',{method:'POST',body:JSON.stringify({})});toast('Demo data reset.');navTo('overview');}catch(error){toast(error.message,'error');}
});
renderCurrent();
