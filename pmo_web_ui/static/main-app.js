  const BASE = '';
  let _currentArtifactModal = null;

  /* ── NAVIGATION ── */
  function navigateTo(page) {
    applyTranslations();
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('page-' + page).classList.add('active');
    const navEl = document.getElementById('nav-' + page);
    if (navEl) navEl.classList.add('active');

    // Load data for the surface
    if (page === 'workspace') loadWorkspaceData();
    if (page === 'deliverables') loadDelProjects();
    if (page === 'acceptance') loadAccProjects();
    if (page === 'advisories') loadAdvProjects();
    if (page === 'review') loadReviewProjects();
    if (page === 'games') loadGamesList();
  applyTranslations();
    if (page === 'status') { /* manual query */ }
    if (page === 'gate') { /* manual query */ }
  }

  /* ── UTILITIES ── */
  

  

  

  

  

  

  


  async function _api(method, url, body) {
    const opts = {method, headers:{'Content-Type':'application/json'}};
    if (body) opts.body = JSON.stringify(body);
    const r = await fetch(BASE + url, opts);
    return r.json();
  }

  


  /* ── GLOBAL PROJECT SELECT ── */
  async function loadGlobalProjects() {
    const sel = document.getElementById('global-project-select');
    try {
      const d = await _api('GET', '/projects');
      if (!d.ok) return;
      const opts = (d.projects || []).map(p =>
        `<option value="${p.project_id}">${_esc(p.project_name)}</option>`
      ).join('');
      sel.innerHTML = '<option value="">Select project…</option>' + opts;
    } catch(e) {}
  }

  async function onGlobalProjectChange() {
    const pid = document.getElementById('global-project-select').value;
    if (!pid) return;
    // Set other selects
    ['del-project-select','acc-project-select','adv-project-select'].forEach(selId => {
      const sel = document.getElementById(selId);
      if (sel) sel.value = pid;
    });
    // Reload Alpine workspace data
    const ws = document.getElementById('page-workspace');
    if (ws && ws.__x) ws.__x.$data.loadProjectData();
    loadWorkspaceData();
  }

  /* ── WORKSPACE ── */
  async function loadWorkspaceData() {
    const pid = document.getElementById('global-project-select').value;
    const empty = document.getElementById('ws-empty');
    const content = document.getElementById('ws-content');

    if (!pid) {
      empty.classList.remove('hidden');
      content.classList.add('hidden');
      return;
    }
    empty.classList.add('hidden');
    content.classList.remove('hidden');

    try {
      const [projRes, artsRes, tasksRes, blkRes, accRes] = await Promise.all([
        fetch(BASE + '/projects/' + encodeURIComponent(pid)),
        fetch(BASE + '/projects/' + encodeURIComponent(pid) + '/artifacts'),
        fetch(BASE + '/projects/' + encodeURIComponent(pid) + '/tasks'),
        fetch(BASE + '/projects/' + encodeURIComponent(pid) + '/blockers'),
        fetch(BASE + '/projects/' + encodeURIComponent(pid) + '/acceptance-package'),
      ]);

      const proj = await projRes.json();
      const arts = await artsRes.json();
      const tasks = tasksRes.json();
      const blks = await blkRes.json();
      const acc = await accRes.json();

      if (!proj.ok) return;

      // Meta
      document.getElementById('ws-proj-name').textContent = _esc(proj.project_name);
      document.getElementById('ws-proj-owner').textContent = _esc(proj.project_owner);
      document.getElementById('ws-proj-status').innerHTML = `<span class="badge ${_badgeClass(proj.project_status)}">${proj.project_status}</span>`;
      document.getElementById('ws-proj-created').textContent = _ts(proj.created_at);
      document.getElementById('ws-project-name').textContent = _esc(proj.project_name);
      document.getElementById('ws-title').textContent = _esc(proj.project_name) + ' — Workspace';
      document.getElementById('ws-proj-goal').textContent = _esc(proj.project_goal) || '—';

      // Pipeline (fake stages since we don't have task stage data here)
      renderPipeline('ws-pipeline', 'current');

      // Task progress (from tasks response)
      let taskTotal = 0, taskDone = 0, taskBlocked = 0;
      try {
        const t = await tasks;
        if (t.ok && t.tasks) {
          taskTotal = t.tasks.length;
          taskDone = t.tasks.filter(x => x.task_status === 'done' || x.task_status === 'complete').length;
          taskBlocked = t.tasks.filter(x => x.task_status === 'blocked').length;
        }
      } catch(e) {}
      document.getElementById('ws-task-total').textContent = taskTotal;
      document.getElementById('ws-task-done').textContent = taskDone;
      document.getElementById('ws-task-blocked').textContent = taskBlocked;

      // Artifact grid
      const complete = proj.artifact_completeness || {};
      const types = [
        {k:'scope', label:'Scope', icon:'📐'},
        {k:'spec', label:'Spec', icon:'📄'},
        {k:'arch', label:'Arch', icon:'🏗️'},
        {k:'testcase', label:'Test Case', icon:'🧪'},
        {k:'testreport', label:'Test Report', icon:'📋'},
        {k:'guideline', label:'Guideline', icon:'📏'},
      ];
      document.getElementById('ws-artifact-grid').innerHTML = types.map(t => {
        const art = complete[t.k];
        const done = art && art.has_content;
        return `<div class="artifact-chip ${done ? 'done' : 'missing'}" onclick="openArtifactModal('${t.k}')">
          <div class="artifact-chip-icon">${done ? '✓' : '○'}</div>
          <div class="artifact-chip-name">${t.icon} ${t.label}</div>
          <div class="artifact-chip-status">${done ? 'Complete' : 'Missing'}</div>
        </div>`;
      }).join('');

      // Blockers
      try {
        const b = await blks;
        const blockers = b.blockers || [];
        if (blockers.length === 0) {
          document.getElementById('ws-blockers-list').innerHTML = '<div class="empty-state" style="padding:1rem">No active blockers. ✓</div>';
        } else {
          document.getElementById('ws-blockers-list').innerHTML = blockers.slice(0,3).map(blk => `
            <div class="signal-item blocker" style="padding:0.5rem 0.75rem">
              <div class="signal-icon" style="color:var(--red)">⚠</div>
              <div class="signal-body">
                <div class="signal-msg" style="font-size:0.82rem">${_esc(blk.reason)}</div>
                <div class="signal-meta">${blk.age_hours || 0}h · ${_ts(blk.detected_at)}</div>
              </div>
              <span class="sev-tag sev-${blk.severity}">${blk.severity}</span>
            </div>
          `).join('');
        }
        // Update advisory badge
        const badge = document.getElementById('advisory-badge');
        if (blockers.length > 0) {
          badge.textContent = blockers.length;
          badge.classList.remove('hidden');
        } else {
          badge.classList.add('hidden');
        }
      } catch(e) {}

      // Acceptance summary
      try {
        const a = await acc;
        if (a.ok && a.acceptance_package) {
          const pkg = a.acceptance_package;
          const badgeClass = pkg.acceptance_decision === 'APPROVED' ? 'badge-complete'
            : pkg.acceptance_decision === 'REJECTED' ? 'badge-shutdown' : 'badge-pending';
          document.getElementById('ws-acceptance-summary').innerHTML = `
            <span class="badge ${badgeClass}">${pkg.acceptance_decision || 'PENDING'}</span>
            <span class="text-dim" style="font-size:0.82rem">${pkg.decision_by ? 'by ' + _esc(pkg.decision_by) : 'Awaiting decision'}</span>
          `;
        } else {
          document.getElementById('ws-acceptance-summary').innerHTML = '<span class="badge badge-missing">NO PACKAGE</span><span class="text-dim" style="font-size:0.82rem">Acceptance package not yet created.</span>';
        }
      } catch(e) {}

      // Output package
      document.getElementById('ws-output-package').innerHTML = `
        <div class="output-package">
          <div class="output-package-icon">📦</div>
          <div class="output-package-info">
            <div class="output-package-name">Project Output Package</div>
            <div class="output-package-meta">${Object.values(complete).filter(a => a && a.has_content).length} artifact(s) ready · Ready for export when acceptance is approved</div>
          </div>
          <div class="output-package-actions">
            <button class="ghost sm" onclick="navigateTo('deliverables')">View Deliverables</button>
          </div>
        </div>
      `;

    } catch(e) {
      console.error('workspace load error', e);
    }
  }

  function renderPipeline(elId, currentStage) {
    const stages = [
      {k:'INTAKE', label:'Intake'},
      {k:'BA', label:'BA'},
      {k:'SA', label:'SA'},
      {k:'DEV', label:'Dev'},
      {k:'QA', label:'QA'},
      {k:'DONE', label:'Done'},
    ];
    const currentIdx = stages.findIndex(s => s.k === currentStage) || 1;
    const el = document.getElementById(elId);
    el.innerHTML = stages.map((s, i) => {
      let cls = '';
      if (i < currentIdx) cls = 'done';
      else if (i === currentIdx) cls = 'current';
      const icon = i < currentIdx ? '✓' : i === currentIdx ? '→' : '';
      return `<div class="pipeline-stage ${cls}">
        <div class="pipeline-icon ${cls}">${icon}</div>
        <div class="pipeline-label">${s.label}</div>
      </div>` + (i < stages.length - 1 ? `<div class="pipeline-connector ${i < currentIdx ? 'done' : ''}"></div>` : '');
    }).join('');
  }

  /* ── INTAKE ── */
  const INTAKE_FIELDS = ['int-name', 'int-owner', 'int-goal'];
  let currentPrereqProjectId = null;

  // Artifact type display names and icons
  const ARTIFACT_META = {
    scope:       { label: 'Scope',         icon: '📐', producer: 'Alex / BA' },
    spec:        { label: 'Specification', icon: '📄', producer: 'BA Agent' },
    arch:        { label: 'Architecture',  icon: '🏗️', producer: 'SA Agent' },
    testcase:    { label: 'Test Case',     icon: '🧪', producer: 'QA Agent' },
    testreport:  { label: 'Test Report',   icon: '📋', producer: 'QA Agent' },
    guideline:   { label: 'Guideline',      icon: '📏', producer: 'Maverick' },
  };
  const ARTIFACT_ORDER = ['scope', 'spec', 'arch', 'testcase', 'testreport', 'guideline'];

  function intakeValidate() {
    const filled = INTAKE_FIELDS.filter(id => {
      const el = document.getElementById(id);
      return el && el.value.trim() !== '';
    });
    const total = INTAKE_FIELDS.length;
    const pct = Math.round((filled.length / total) * 100);

    const fill = document.getElementById('int-phase1-fill');
    if (fill) {
      fill.style.width = pct + '%';
      fill.className = 'progress-fill ' + (pct === 100 ? 'ok' : pct > 0 ? 'partial' : 'empty');
      document.getElementById('int-phase1-count').textContent = `${filled.length} / ${total} required`;
    }

    // Field-level states
    INTAKE_FIELDS.forEach(id => {
      const el = document.getElementById(id);
      const state = document.getElementById(id + '-state');
      if (!el || !state) return;
      if (el.value.trim()) {
        state.className = 'field-state filled';
        state.textContent = '✓ Filled';
      } else {
        state.className = 'field-state missing';
        state.textContent = '⚠ Required — not provided';
      }
    });

    const btn = document.getElementById('int-create-btn');
    if (btn) btn.disabled = filled.length < total;
  }

  function intakeReset() {
    INTAKE_FIELDS.forEach(id => {
      const el = document.getElementById(id);
      if (el) { el.value = ''; if (el.tagName === 'SELECT') el.selectedIndex = 0; }
    });
    const delType = document.getElementById('int-deliverable-type');
    if (delType) delType.selectedIndex = 0;
    intakeValidate();
    document.getElementById('int-output').textContent = 'Form cleared.';
    document.getElementById('int-output').className = 'output';
  }

  async function doIntakeCreate() {
    const name = document.getElementById('int-name').value.trim();
    const owner = document.getElementById('int-owner').value.trim();
    const goal = document.getElementById('int-goal').value.trim();
    const deliverableType = document.getElementById('int-deliverable-type').value;
    const out = document.getElementById('int-output');

    if (!name || !owner || !goal) {
      _warn(out, 'Name, Owner, and Goal are required.');
      return;
    }

    _neutral(out, 'Creating project…');
    try {
      const d = await _api('POST', '/projects', {
        project_name: name,
        project_owner: owner,
        project_goal: goal,
        domain_type: 'internal',
        intake_summary: '',
        intake_deliverable: deliverableType || '',
        intake_business_context: '',
        actor: 'alex',
      });
      if (d.ok) {
        currentPrereqProjectId = d.project_id;
        _ok(out, `Project created: ${d.project_id}. Now submit the prerequisite package.`);

        // Show project info
        document.getElementById('int-proj-info').textContent =
          `${name} · ${d.project_status} · Owner: ${owner}`;

        // Show Phase 2
        document.getElementById('int-phase2').style.display = 'block';
        document.getElementById('int-phase1-progress').style.display = 'none';
        document.getElementById('int-create-btn').disabled = true;
        document.getElementById('int-create-btn').textContent = '✓ Project Created';

        // Load and render prerequisite package
        await loadPrereqPackage(d.project_id);

        // Sync global project list
        await loadGlobalProjects();
        document.getElementById('global-project-select').value = d.project_id;
      } else {
        _err(out, d.message || 'Failed to create project.');
      }
    } catch(e) { _err(out, e.message); }
  }

  async function loadPrereqPackage(projectId) {
    const list = document.getElementById('int-prereq-list');
    list.innerHTML = '<div class="empty-state" style="padding:1rem">Loading prerequisite package…</div>';
    try {
      const d = await _api('GET', `/projects/${projectId}/prerequisites`);
      if (!d.ok) { list.innerHTML = '<div class="empty-state">Failed to load prerequisites.</div>'; return; }
      renderPrereqPackage(d);
    } catch(e) {
      list.innerHTML = `<div class="empty-state">Error: ${e.message}</div>`;
    }
  }

  function renderPrereqPackage(d) {
    const list = document.getElementById('int-prereq-list');
    const submitted = d.prerequisite_submitted || 0;
    const total = 6;
    const pct = Math.round((submitted / total) * 100);

    // Update progress
    const fill = document.getElementById('int-prereq-fill');
    fill.style.width = pct + '%';
    fill.className = 'progress-fill ' + (pct === 100 ? 'ok' : pct > 0 ? 'partial' : 'empty');
    document.getElementById('int-prereq-count').textContent = `${submitted} / ${total} submitted`;

    // Render cards
    list.innerHTML = ARTIFACT_ORDER.map(at => {
      const meta = ARTIFACT_META[at];
      const pa = d.artifacts && d.artifacts[at] ? d.artifacts[at] : null;
      return renderPrereqCard(at, meta, pa || { submitted: false });
    }).join('');

    // Show proceed button when all 6 are submitted
    const proceedSection = document.getElementById('int-proceed-section');
    if (d.prerequisite_complete) {
      proceedSection.style.display = 'block';
    } else {
      proceedSection.style.display = 'none';
    }
  }

  function renderPrereqCard(at, meta, pa) {
    const statusClass = pa.submitted ? 'submitted' : 'pending';
    const statusIcon = pa.submitted ? '✓' : '○';
    const statusLabel = pa.submitted ? 'Submitted' : 'Pending';
    const submittedAt = pa.submitted_at ? new Date(pa.submitted_at).toLocaleString() : '';

    if (pa.submitted) {
      return `
      <div class="card prereq-card ${statusClass}" id="prereq-card-${at}">
        <div class="prereq-card-header">
          <div class="prereq-icon">${meta.icon}</div>
          <div class="prereq-title">${meta.label}</div>
          <div class="prereq-status submitted">✓ Submitted</div>
        </div>
        <div class="prereq-meta">
          <span>Producer: ${_esc(pa.producer || meta.producer)}</span>
          ${submittedAt ? `<span>${submittedAt}</span>` : ''}
        </div>
        ${pa.content_preview ? `<div class="prereq-preview">${_esc(pa.content_preview)}</div>` : ''}
      </div>`;
    } else {
      return `
      <div class="card prereq-card pending" id="prereq-card-${at}">
        <div class="prereq-card-header">
          <div class="prereq-icon">${meta.icon}</div>
          <div class="prereq-title">${meta.label}</div>
          <div class="prereq-status pending">○ Pending</div>
        </div>
        <div class="prereq-form">
          <textarea id="prereq-content-${at}" rows="2" placeholder="Brief description or summary of this ${meta.label.toLowerCase()}…"></textarea>
          <div class="prereq-producer-row">
            <input id="prereq-producer-${at}" type="text" placeholder="Producer (e.g. ${meta.producer})" value="${meta.producer}" />
            <button class="primary sm" onclick="submitPrereq('${at}')">Submit</button>
          </div>
        </div>
      </div>`;
    }
  }

  async function submitPrereq(artifactType) {
    const projectId = currentPrereqProjectId;
    if (!projectId) return;

    const contentEl = document.getElementById(`prereq-content-${artifactType}`);
    const producerEl = document.getElementById(`prereq-producer-${artifactType}`);
    const content = contentEl ? contentEl.value.trim() : '';
    const producer = producerEl ? producerEl.value.trim() : '';

    // Minimum content enforcement
    if (content.length < 10) {
      alert('Content must be at least 10 characters describing this prerequisite document.');
      if (contentEl) contentEl.focus();
      return;
    }

    try {
      const d = await _api('POST', `/projects/${projectId}/prerequisites`, {
        artifact_type: artifactType,
        content_preview: content,
        producer: producer,
        actor: 'alex',
      });
      if (d.ok) {
        // Re-render the package
        await loadPrereqPackage(projectId);
      } else {
        alert('Failed to submit: ' + (d.message || d.error));
      }
    } catch(e) { alert('Error: ' + e.message); }
  }

  function doProceedToReview() {
    // Placeholder: Sprint 2R will wire up pre-kickoff review surface
    navigateTo('review'); doLoadReview();
  }

  /* ── DELIVERABLES BROWSER ── */
  async function loadDelProjects() {
    const sel = document.getElementById('del-project-select');
    try {
      const d = await _api('GET', '/projects');
      if (!d.ok) return;
      sel.innerHTML = '<option value="">— Select project —</option>' +
        (d.projects || []).map(p => `<option value="${p.project_id}">${_esc(p.project_name)}</option>`).join('');
      // If global project is selected, sync
      const gp = document.getElementById('global-project-select').value;
      if (gp) sel.value = gp;
    } catch(e) {}
  }

  async function loadDeliverables() {
    const pid = document.getElementById('del-project-select').value;
    const list = document.getElementById('del-list');
    if (!pid) { list.innerHTML = '<div class="empty-state">Select a project to browse its deliverables.</div>'; return; }
    list.innerHTML = '<div class="empty-state">Loading…</div>';
    try {
      const d = await _api('GET', '/projects/' + encodeURIComponent(pid) + '/artifacts');
      if (!d.ok) { list.innerHTML = '<div class="empty-state">Failed to load artifacts.</div>'; return; }
      window._cachedDeliverables = { pid, artifacts: d.artifacts || [] };
      renderDeliverableList();
    } catch(e) { list.innerHTML = '<div class="empty-state">Cannot reach PMO backend.</div>'; }
  }

  function renderDeliverableList() {
    const cache = window._cachedDeliverables;
    if (!cache) return;
    const pid = cache.pid;
    const arts = cache.artifacts || [];
    const category = document.getElementById('del-category').value;
    const filter = document.getElementById('del-filter').value;
    const search = (document.getElementById('del-search').value || '').toLowerCase();

    const typeInfo = {
      scope:  {label:'Scope',         icon:'📐'},
      spec:   {label:'Specification', icon:'📄'},
      arch:   {label:'Architecture',   icon:'🏗️'},
      testcase:{label:'Test Case',    icon:'🧪'},
      testreport:{label:'Test Report',icon:'📋'},
      guideline:{label:'Guideline',   icon:'📏'},
    };

    const allTypes = Object.keys(typeInfo);
    let items = allTypes.map(t => {
      const art = arts.find(a => a.artifact_type === t);
      return { type: t, art, info: typeInfo[t] };
    });

    if (category === 'prerequisite') items = items.filter(x => x.art && x.art.category === 'prerequisite');
    if (category === 'delivery') items = items.filter(x => x.art && x.art.category === 'delivery');
    if (filter === 'complete') items = items.filter(x => x.art && x.art.content);
    if (filter === 'missing') items = items.filter(x => !x.art || !x.art.content);
    if (search) items = items.filter(x =>
      (x.art && x.art.content && x.art.content.toLowerCase().includes(search)) ||
      x.info.label.toLowerCase().includes(search)
    );

    const list = document.getElementById('del-list');
    if (items.length === 0) {
      list.innerHTML = '<div class="empty-state">No artifacts match the current filter.</div>';
      return;
    }

    list.innerHTML = `<div class="section-header mb-1">
      <div class="section-title">Artifacts (${items.length})</div>
    </div>
    <div class="deliverable-list">${items.map(item => {
      const { type, art, info } = item;
      const done = art && art.content;
      const catBadge = art && art.category === 'prerequisite'
        ? '<span class="badge" style="background:#e8f5e9;color:#2e7d32;font-size:0.62rem;padding:1px 6px;border-radius:4px">pkg</span>'
        : art && art.category === 'delivery'
        ? '<span class="badge" style="background:#e3f2fd;color:#1565c0;font-size:0.62rem;padding:1px 6px;border-radius:4px">del</span>'
        : '';
      return `<div class="deliverable-card ${done ? 'complete' : 'missing'}">
        <div class="deliverable-header">
          <div class="deliverable-icon">${info.icon}</div>
          <div class="deliverable-info">
            <div class="deliverable-name">${info.label}</div>
            <div class="deliverable-meta">${art && art.produced_by ? 'Produced by: ' + _esc(art.produced_by) + ' · ' : ''}${art && art.produced_at ? _ts(art.produced_at) : 'Not yet produced'}</div>
          </div>
          <div class="deliverable-status">
            ${catBadge}
            ${done
              ? '<span class="badge badge-complete">✓ Complete</span>'
              : '<span class="badge badge-missing">○ Missing</span>'
            }
          </div>
        </div>
        ${done && art.content
          ? `<div class="deliverable-preview">${_esc(art.content.substring(0, 200))}${art.content.length > 200 ? '…' : ''}</div>
             <div class="deliverable-actions">
               <button class="ghost sm" onclick="openArtifactContent('${type}')">View Full</button>
               <button class="ghost sm" onclick="doExportArtifact('${pid}','${type}')">Export</button>
             </div>`
          : `<div class="deliverable-actions">
               <button class="secondary sm" onclick="doRequestArtifact('${type}')">Request from Agent</button>
             </div>`
        }
      </div>`;
    }).join('')}</div>`;
  }

  /* ── ARTIFACT MODAL ── */
  async function openArtifactContent(type) {
    const cache = window._cachedDeliverables;
    if (!cache) return;
    const art = cache.artifacts.find(a => a.artifact_type === type);
    if (!art) return;
    const pid = cache.pid;
    // Fetch full content via dedicated endpoint
    if (art.artifact_id) {
      try {
        const d = await _api('GET', '/projects/' + encodeURIComponent(pid) + '/artifacts/' + encodeURIComponent(art.artifact_id));
        if (d.ok && d.artifact) {
          openArtifactModal(type, d.artifact.content || '(No content)');
          return;
        }
      } catch(e) { /* fall through to preview */ }
    }
    // Fallback to preview if fetch fails
    openArtifactModal(type, art.content_preview || '(No content available)');
  }

  function openArtifactModal(type, content) {
    const typeInfo = {
      scope:'📐 Scope', spec:'📄 Specification', arch:'🏗️ Architecture',
      testcase:'🧪 Test Case', testreport:'📋 Test Report', guideline:'📏 Guideline'
    };
    document.getElementById('modal-artifact-title').textContent = typeInfo[type] || type;
    document.getElementById('modal-artifact-body').textContent = content || '(No content)';
    document.getElementById('artifact-modal').classList.remove('hidden');
    _currentArtifactModal = { type, content };
  }

  function closeArtifactModal() {
    document.getElementById('artifact-modal').classList.add('hidden');
    _currentArtifactModal = null;
  }

  function modalExport() {
    if (!_currentArtifactModal) return;
    const { type, content } = _currentArtifactModal;
    const blob = new Blob([content || ''], {type: 'text/plain'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${type}-artifact.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function doExportArtifact(pid, type) {
    const cache = window._cachedDeliverables;
    if (!cache) return;
    const art = cache.artifacts.find(a => a.artifact_type === type);
    if (!art || !art.artifact_id) return;
    try {
      const d = await _api('GET', '/projects/' + encodeURIComponent(pid) + '/artifacts/' + encodeURIComponent(art.artifact_id));
      if (d.ok && d.artifact && d.artifact.content) {
        const blob = new Blob([d.artifact.content], {type: 'text/plain'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${type}-artifact.txt`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch(e) {}
  }

  async function doRequestArtifact(type) {
    alert(`Request for "${type}" artifact from agent.\n\nNot implemented in Sprint 3R.\n\nThis feature will be built in a future sprint.`);
  }

  /* ── ACCEPTANCE ── */
  async function loadAccProjects() {
    const sel = document.getElementById('acc-project-select');
    try {
      const d = await _api('GET', '/projects');
      if (!d.ok) return;
      sel.innerHTML = '<option value="">— Select project —</option>' +
        (d.projects || []).map(p => `<option value="${p.project_id}">${_esc(p.project_name)}</option>`).join('');
      const gp = document.getElementById('global-project-select').value;
      if (gp) sel.value = gp;
    } catch(e) {}
  }

  async function loadAcceptance() {
    const pid = document.getElementById('acc-project-select').value;
    const content = document.getElementById('acc-content');
    if (!pid) { content.innerHTML = '<div class="empty-state">Select a project to review its acceptance package.</div>'; return; }
    content.innerHTML = '<div class="empty-state">Loading…</div>';

    try {
      const [projRes, accRes, artsRes, outRes] = await Promise.all([
        fetch(BASE + '/projects/' + encodeURIComponent(pid)),
        fetch(BASE + '/projects/' + encodeURIComponent(pid) + '/acceptance-package'),
        fetch(BASE + '/projects/' + encodeURIComponent(pid) + '/artifacts'),
        fetch(BASE + '/projects/' + encodeURIComponent(pid) + '/output-package'),
      ]);

      const proj = await projRes.json();
      const acc = await accRes.json();
      const arts = await artsRes.json();
      const out = await outRes.json();
      const outputPackage = out.ok ? (out.output_package || null) : null;
      const isIndependentlyDeliverable = outputPackage && outputPackage.is_complete;

      if (!proj.ok) { content.innerHTML = '<div class="empty-state">Failed to load project.</div>'; return; }

      const complete = proj.artifact_completeness || {};
      const types = [
        {k:'scope', label:'Scope', icon:'📐'},
        {k:'spec', label:'Spec', icon:'📄'},
        {k:'arch', label:'Arch', icon:'🏗️'},
        {k:'testcase', label:'Test Case', icon:'🧪'},
        {k:'testreport', label:'Test Report', icon:'📋'},
        {k:'guideline', label:'Guideline', icon:'📏'},
      ];

      const pkg = acc.ok && acc.acceptance_package ? acc.acceptance_package : null;
      const badgeClass = !pkg ? 'badge-missing'
        : pkg.acceptance_decision === 'APPROVED' ? 'badge-complete'
        : pkg.acceptance_decision === 'REJECTED' ? 'badge-shutdown' : 'badge-pending';

      // Decision history (simulated from acceptance package)
      const history = pkg && pkg.decision_history ? pkg.decision_history : [];

      // Closure readiness
      const completeCount = types.filter(t => complete[t.k] && complete[t.k].has_content).length;
      const allComplete = completeCount === types.length;
      const hasDecision = pkg && pkg.acceptance_decision;
      const isApproved = pkg && pkg.acceptance_decision === 'APPROVED';

      content.innerHTML = `
        <!-- Acceptance Package Card -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">Acceptance Package</div>
            <span class="badge ${badgeClass}">${pkg ? (pkg.acceptance_decision || 'PENDING') : 'NO PACKAGE'}</span>
          </div>

          <!-- Artifact completeness -->
          <div style="margin-bottom:1rem">
            <div class="section-title mb-1">Artifact Completeness</div>
            <div class="artifact-grid">
              ${types.map(t => {
                const done = complete[t.k] && complete[t.k].has_content;
                return `<div class="artifact-chip ${done ? 'done' : 'missing'}">
                  <div class="artifact-chip-icon">${done ? '✓' : '○'}</div>
                  <div class="artifact-chip-name">${t.icon} ${t.label}</div>
                  <div class="artifact-chip-status">${done ? 'Complete' : 'Missing'}</div>
                </div>`;
              }).join('')}
            </div>
          </div>

          ${pkg ? `
            ${pkg.verification_notes ? `<div style="font-size:0.85rem;color:var(--text-dim);margin-bottom:0.75rem;padding:0.5rem 0.75rem;background:var(--surface);border-radius:6px;border-left:2px solid var(--border-light)">${_esc(pkg.verification_notes)}</div>` : ''}
            <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:0.75rem">
              ${pkg.decision_by ? 'By: ' + _esc(pkg.decision_by) + ' · ' : ''}
              ${pkg.decided_at ? _ts(pkg.decided_at) : 'Decision not yet recorded'}
            </div>
          ` : ''}

          ${!pkg || !pkg.acceptance_decision ? `
            <div class="section-title mb-1">Review & Decision</div>
            <div class="form-row" style="margin-bottom:0.75rem">
              <div class="field" style="flex:2">
                <label>Verification notes</label>
                <textarea id="acc-note" rows="3" placeholder="Document your review findings before approving or requesting revision..."></textarea>
              </div>
            </div>
            <div class="flex gap-05">
              <button class="success" onclick="doApproveAcceptance('${pid}')">✓ Approve &amp; Close</button>
              <button class="danger" onclick="doRejectAcceptance('${pid}')">Request Revision</button>
            </div>
          ` : `
            <div class="output ok" style="margin-top:0.75rem">Decision recorded: ${pkg.acceptance_decision}</div>
          `}
        </div>

        <!-- Decision History -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">Decision History</div>
          </div>
          ${history.length > 0 ? `
            <div class="history-list">
              ${history.map(h => `
                <div class="history-item">
                  <div class="history-time">${_ts(h.timestamp)}</div>
                  <div class="history-text">
                    <span class="history-actor">${_esc(h.actor)}</span>
                    ${_esc(h.action)}
                    ${h.note ? ': ' + _esc(h.note) : ''}
                  </div>
                </div>
              `).join('')}
            </div>
          ` : '<div class="empty-state" style="padding:1rem">No decision history yet.</div>'}
        </div>

        <!-- Output Package -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">${T[T.currLang].acc_output_package}</div>
            ${isIndependentlyDeliverable ? '<span class="badge badge-deliverable">' + T[T.currLang].acc_independently_deliverable + '</span>' : ''}
          </div>
          <div class="output-package">
            <div class="output-package-icon">📦</div>
            <div class="output-package-info">
              <div class="output-package-name">Exportable Deliverable: ${isApproved ? 'READY' : 'PENDING APPROVAL'}</div>
              <div class="output-package-meta">${completeCount} artifact(s) available · ${types.length - completeCount} missing</div>
              ${!allComplete ? `<div style="font-size:0.75rem;color:var(--amber);margin-top:0.2rem">Note: ${types.length - completeCount} artifact(s) still missing — output package is partial</div>` : ''}
            </div>
            <div class="output-package-actions">
              <button class="ghost sm" onclick="navigateTo('deliverables')">${T[T.currLang].acc_preview_package}</button>
              <button class="secondary sm" ${!isApproved ? 'disabled' : ''} onclick="doExportPackage('${pid}')">${T[T.currLang].acc_download_package}</button>
            </div>
          </div>
        </div>

        <!-- Closure Readiness -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">${T[T.currLang].acc_closure_readiness}</div>
          </div>
          <div class="checklist">
            <div class="checklist-item">
              <div class="checklist-icon ${proj.project_status !== 'active' && proj.project_status ? 'done' : 'pending'}">${proj.project_status !== 'active' && proj.project_status ? '✓' : '○'}</div>
              <div class="checklist-text">Project past DEV stage</div>
            </div>
            <div class="checklist-item">
              <div class="checklist-icon ${completeCount > 0 ? 'done' : 'pending'}">${completeCount > 0 ? '✓' : '○'}</div>
              <div class="checklist-text">At least one artifact produced</div>
            </div>
            <div class="checklist-item ${allComplete ? '' : 'pending'}">
              <div class="checklist-icon ${allComplete ? 'done' : 'pending'}">${allComplete ? '✓' : '○'}</div>
              <div class="checklist-text">All required artifacts present</div>
            </div>
            <div class="checklist-item ${hasDecision ? '' : 'pending'}">
              <div class="checklist-icon ${hasDecision ? 'done' : 'pending'}">${hasDecision ? '✓' : '○'}</div>
              <div class="checklist-text">Acceptance decision recorded</div>
            </div>
          </div>
          <div style="margin-top:0.75rem;padding:0.5rem 0.75rem;background:var(--surface);border-radius:6px;font-size:0.8rem">
            Closure readiness: <strong class="${allComplete && hasDecision ? 'text-green' : 'text-amber'}">
              ${allComplete && hasDecision ? 'READY' : 'PARTIAL (' + [allComplete ? 1 : 0, hasDecision ? 1 : 0, completeCount > 0 ? 1 : 0, proj.project_status !== 'active' ? 1 : 0].filter(Boolean).length + '/4 conditions met)'}
            </strong>
          </div>
        </div>
      `;
    } catch(e) {
      content.innerHTML = '<div class="empty-state">Cannot reach PMO backend.</div>';
    }
  }

  async function doApproveAcceptance(pid) {
    const note = document.getElementById('acc-note')?.value.trim() || '';
    const actor = prompt('Your name (for the decision record):');
    if (!actor) return;
    const d = await _api('POST', '/projects/' + encodeURIComponent(pid) + '/acceptance-package/approve', {actor, note});
    if (d.ok) await loadAcceptance();
    else alert(d.message || 'Failed');
  }

  async function doRejectAcceptance(pid) {
    const reason = document.getElementById('acc-note')?.value.trim();
    if (!reason) { alert('Please enter a reason for requesting revision.'); return; }
    const actor = prompt('Your name (for the decision record):');
    if (!actor) return;
    const d = await _api('POST', '/projects/' + encodeURIComponent(pid) + '/acceptance-package/reject', {actor, reason});
    if (d.ok) await loadAcceptance();
    else alert(d.message || 'Failed');
  }

  async function doExportPackage(pid) {
    const d = await _api('GET', '/projects/' + encodeURIComponent(pid) + '/output-package');
    if (!d.ok || !d.output_package) {
      alert(d.message || 'Output package not available.');
      return;
    }
    const pkg = d.output_package;
    const arts = pkg.artifacts || [];
    const complete = pkg.is_complete ? 'COMPLETE' : 'PARTIAL';
    let content = `Project Output Package\n${'='.repeat(40)}\nPackage ID: ${pkg.package_id}\nStatus: ${complete}\nArtifacts: ${arts.length}\n${'='.repeat(40)}\n\n`;
    arts.forEach(a => {
      content += `[${a.artifact_type}] ${a.display_name}\n${'-'.repeat(40)}\n${a.content || '(no content)'}\n\n`;
    });
    const blob = new Blob([content], {type: 'text/plain'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'output-package.txt';
    a.click();
    URL.revokeObjectURL(url);
  }

  /* ── STATUS ── */
  async function doStatus() {
    const taskId = document.getElementById('status-task-id').value.trim();
    const out = document.getElementById('status-output');
    if (!taskId) { _warn(out, 'Enter a task ID.'); return; }
    _neutral(out, 'Loading…');
    const d = await _api('GET', '/status/' + encodeURIComponent(taskId));
    if (d.ok) { _ok(out, JSON.stringify(d, null, 2)); }
    else { _err(out, d.message || 'Failed'); }
  }

  async function doListTasks() {
    const pid = document.getElementById('list-project-id').value.trim();
    const out = document.getElementById('list-output');
    if (!pid) { _warn(out, 'Enter a project ID.'); return; }
    _neutral(out, 'Loading…');
    const d = await _api('GET', '/projects/' + encodeURIComponent(pid) + '/tasks');
    if (d.ok) { _ok(out, JSON.stringify(d, null, 2)); }
    else { _err(out, d.message || 'Failed'); }
  }

  /* ── ADVISORIES ── */
  async function loadAdvProjects() {
    const sel = document.getElementById('adv-project-select');
    try {
      const d = await _api('GET', '/projects');
      if (!d.ok) return;
      sel.innerHTML = '<option value="">— Select project —</option>' +
        (d.projects || []).map(p => `<option value="${p.project_id}">${_esc(p.project_name)}</option>`).join('');
    } catch(e) {}
  }

  async function loadAdvisories() {
    const pid = document.getElementById('adv-project-select').value;
    const panel = document.getElementById('adv-list');
    if (!pid) { panel.innerHTML = '<div class="empty-state">Select a project to view advisories.</div>'; return; }
    panel.innerHTML = '<div class="empty-state">Loading…</div>';
    try {
      const [advRes, blkRes] = await Promise.all([
        fetch(BASE + '/projects/' + encodeURIComponent(pid) + '/advisories'),
        fetch(BASE + '/projects/' + encodeURIComponent(pid) + '/blockers'),
      ]);
      const advs = await advRes.json();
      const blks = await blkRes.json();
      const blockers = blks.blockers || [];
      const advisories = (advs.advisories || []).filter(a => !a.acknowledged);
      let html = '';

      if (blockers.length > 0) {
        html += `<div class="mb-1">
          <div class="section-title mb-1" style="color:var(--red)">⚠ Blockers (${blockers.length})</div>
          <div class="signal-list">
            ${blockers.map(b => `
              <div class="signal-item blocker">
                <div class="signal-icon" style="color:var(--red)">⚠</div>
                <div class="signal-body">
                  <div class="signal-msg">${_esc(b.reason)}</div>
                  <div class="signal-meta">Task: ${_esc(b.task_id)} · ${b.age_hours || 0}h old · ${_ts(b.detected_at)}</div>
                </div>
                <div class="signal-right">
                  <span class="sev-tag sev-${b.severity}">${b.severity}</span>
                  <button class="secondary sm" onclick="doResolveBlocker('${pid}','${b.blocker_id}')">Resolve</button>
                </div>
              </div>
            `).join('')}
          </div>
        </div>`;
      }

      if (advisories.length > 0) {
        html += `<div>
          <div class="section-title mb-1">📋 Advisories (${advisories.length})</div>
          <div class="signal-list">
            ${advisories.map(a => {
              const icon = {risk:'⚠️',schedule:'⏱',stage:'→',blocker:'🚧'}[a.advisory_type] || 'ℹ️';
              const sevClass = a.severity === 'critical' ? 'sev-critical' : a.severity === 'warn' ? 'sev-warn' : 'sev-info';
              return `<div class="signal-item ${a.severity === 'critical' ? 'blocker' : a.severity === 'warn' ? 'warn' : ''}">
                <div class="signal-icon">${icon}</div>
                <div class="signal-body">
                  <div class="signal-msg">[${a.advisory_type}] ${_esc(a.message)}</div>
                  <div class="signal-meta">${a.task_id ? 'Task: ' + _esc(a.task_id) + ' · ' : ''}Stage: ${a.stage || '—'} · ${_ts(a.created_at)}</div>
                </div>
                <div class="signal-right">
                  <span class="sev-tag ${sevClass}">${a.severity}</span>
                  <button class="secondary sm" onclick="doAckAdvisory('${pid}','${a.advisory_id}')">Dismiss</button>
                </div>
              </div>`;
            }).join('')}
          </div>
        </div>`;
      }

      if (!html) html = '<div class="empty-state">No active advisories or blockers. ✓</div>';
      panel.innerHTML = html;
    } catch(e) { panel.innerHTML = '<div class="empty-state">Cannot reach PMO backend.</div>'; }
  }

  /* ── GAME PRODUCTION (Sprint 4R) ── */

  async function loadGamesList() {
    const list = document.getElementById('games-list');
    if (!list) return;
    list.innerHTML = '<div class="empty-state">Loading…</div>';
    try {
      const d = await _api('GET', '/games');
      if (!d.ok) { list.innerHTML = '<div class="empty-state">Failed to load games.</div>'; return; }
      const games = d.games || [];
      if (games.length === 0) {
        list.innerHTML = '<div class="empty-state">No games yet. Create one above.</div>';
        return;
      }
      let html = '<table class="data-table"><thead><tr><th>Title</th><th>Stage</th><th>Status</th><th>Owner</th><th>Viper</th><th></th></tr></thead><tbody>';
      for (const g of games) {
        html += '<tr>';
        html += '<td>' + _esc(g.title) + '</td>';
        html += '<td><span class="stage-tag">' + _esc(g.current_stage) + '</span></td>';
        html += '<td>' + _esc(g.task_status) + '</td>';
        html += '<td>' + _esc(g.owner || '—') + '</td>';
        html += '<td>' + (g.viper_triggered ? '<span class="sev-tag sev-high">Yes</span>' : '—') + '</td>';
        html += '<td><button class="secondary sm" onclick="selectGame(\'' + g.game_id + '\')">View</button></td>';
        html += '</tr>';
      }
      html += '</tbody></table>';
      list.innerHTML = html;
    } catch(e) {
      list.innerHTML = '<div class="empty-state">Failed to load games.</div>';
    }
  }

  let _selectedGameId = null;

  async function doCreateGame() {
    const title = document.getElementById('game-title').value.trim();
    const owner = document.getElementById('game-owner').value.trim();
    if (!title || !owner) { alert('Title and Owner are required.'); return; }
    const btn = document.getElementById('btn-create-game');
    btn.disabled = true;
    btn.textContent = 'Creating…';
    try {
      const d = await _api('POST', '/games', { title, owner });
      if (!d.ok) { alert('Failed: ' + d.message); return; }
      document.getElementById('game-title').value = '';
      document.getElementById('game-owner').value = '';
      await loadGamesList();
      if (d.game_id) await selectGame(d.game_id);
    } finally {
      btn.disabled = false;
      btn.textContent = '+ Create Game';
    }
  }

  async function selectGame(gameId) {
    _selectedGameId = gameId;
    const detail = document.getElementById('game-detail');
    if (!detail) return;
    detail.classList.remove('hidden');
    await gdRefresh();
    detail.scrollIntoView({ behavior: 'smooth' });
  }

  async function gdRefresh() {
    if (!_selectedGameId) return;
    try {
      const d = await _api('GET', '/games/' + encodeURIComponent(_selectedGameId));
      if (!d.ok) return;

      document.getElementById('gd-title').textContent = d.title || '—';
      document.getElementById('gd-stage').textContent = d.current_stage || '—';
      document.getElementById('gd-status').textContent = d.task_status || '—';
      document.getElementById('gd-owner').textContent = d.owner || '—';

      const gf = d.game_fields || {};
      const triggered = gf.viper_triggered;
      const triggerText = triggered ? 'YES — ' + (gf.trigger_note || '') : 'No';
      document.getElementById('gd-trigger').textContent = triggerText;

      // Escalation
      const esc = gf.escalation;
      const escEl = document.getElementById('gd-escalation');
      if (esc && esc.escalated) {
        escEl.classList.remove('hidden');
        const txt = document.getElementById('gd-esc-reason-text');
        if (txt) txt.textContent = esc.reason + ' by ' + esc.by;
      } else {
        escEl.classList.add('hidden');
      }

      // Populate stage advance select
      const nextStage = document.getElementById('gd-next-stage');
      const stage = d.current_stage;
      const transitions = {
        'CONCEPT': ['GAME_SPEC'],
        'GAME_SPEC': ['PRODUCTION_PREP'],
        'PRODUCTION_PREP': ['PRODUCTION_BUILD'],
        'PRODUCTION_BUILD': ['QA_PLAYTEST'],
        'QA_PLAYTEST': ['ACCEPTANCE_DELIVERY'],
        'ACCEPTANCE_DELIVERY': []
      };
      const allowed = transitions[stage] || [];
      let opts = '<option value="">— select —</option>';
      for (const s of allowed) opts += '<option value="' + s + '">' + s + '</option>';
      nextStage.innerHTML = opts;

      // Show viper row only at PRODUCTION_PREP boundary
      const vRow = document.getElementById('gd-viper-row');
      if (vRow) vRow.classList.toggle('hidden', stage !== 'PRODUCTION_PREP');

      // Show concept approval note only at CONCEPT stage
      const cRow = document.getElementById('gd-concept-row');
      if (cRow) cRow.classList.toggle('hidden', stage !== 'CONCEPT');

    } catch(e) {
      console.error('gdRefresh failed:', e);
    }
  }

  async function doAdvanceStage() {
    if (!_selectedGameId) return;
    const nextStage = document.getElementById('gd-next-stage').value;
    const artifactId = document.getElementById('gd-artifact-id').value.trim();
    const viperTrigger = document.getElementById('gd-viper-trigger').value === 'true';
    const triggerNote = document.getElementById('gd-trigger-note').value.trim();
    const approvalNote = document.getElementById('gd-approval-note').value.trim();
    const msg = document.getElementById('gd-adv-msg');
    if (!nextStage) { if (msg) msg.textContent = 'Select a next stage.'; return; }
    if (msg) msg.textContent = '…';

    const body = {
      new_stage: nextStage,
      actor: 'PMO',
      concept_approved: nextStage === 'GAME_SPEC'
    };
    if (artifactId) body.artifact_id = artifactId;
    if (viperTrigger) { body.viper_triggered = true; body.trigger_note = triggerNote; }
    if (approvalNote) body.approval_note = approvalNote;

    try {
      const d = await _api('POST', '/games/' + encodeURIComponent(_selectedGameId) + '/stage', body);
      if (!d.ok) { if (msg) msg.textContent = 'Error: ' + d.message; return; }
      if (msg) msg.textContent = 'Advanced to ' + nextStage + '.';
      await gdRefresh();
      await loadGamesList();
    } catch(e) {
      if (msg) msg.textContent = 'Failed: ' + e.message;
    }
  }

  async function doSubmitSR() {
    if (!_selectedGameId) return;
    const stage = document.getElementById('gd-sr-stage').value.trim();
    const status = document.getElementById('gd-sr-status').value.trim();
    const progress = document.getElementById('gd-sr-progress').value.trim();
    const blocker = document.getElementById('gd-sr-blocker').value.trim();
    const nextAction = document.getElementById('gd-sr-next').value.trim();
    const msg = document.getElementById('gd-sr-msg');
    if (!stage || !status || !progress || !nextAction) {
      if (msg) msg.textContent = 'Stage, Status, Progress, Next Action are required.'; return;
    }
    if (msg) msg.textContent = '…';
    try {
      const d = await _api('POST', '/games/' + encodeURIComponent(_selectedGameId) + '/status-report', {
        stage, status, progress, next_action: nextAction, blocker, actor: 'PMO'
      });
      if (msg) msg.textContent = d.ok ? 'Status report submitted.' : 'Error: ' + d.message;
    } catch(e) {
      if (msg) msg.textContent = 'Failed: ' + e.message;
    }
  }

  async function doEscalate() {
    if (!_selectedGameId) return;
    const reason = document.getElementById('gd-esc-reason-input').value.trim();
    const msg = document.getElementById('gd-esc-msg');
    if (!reason) { if (msg) msg.textContent = 'Reason is required.'; return; }
    if (msg) msg.textContent = '…';
    try {
      const d = await _api('POST', '/games/' + encodeURIComponent(_selectedGameId) + '/escalate', { reason, actor: 'PMO' });
      if (msg) msg.textContent = d.ok ? 'Escalation raised.' : 'Error: ' + d.message;
      if (d.ok) await gdRefresh();
    } catch(e) {
      if (msg) msg.textContent = 'Failed: ' + e.message;
    }
  }

  async function doResolveBlocker(pid, blockerId) {
    const actor = prompt('Your name:');
    if (!actor) return;
    const d = await _api('POST', '/projects/' + encodeURIComponent(pid) + '/blockers/' + blockerId + '/resolve', {resolved_by: actor});
    if (d.ok) await loadAdvisories();
    else alert(d.message || 'Failed');
  }

  async function doAckAdvisory(pid, advisoryId) {
    const d = await _api('POST', '/projects/' + encodeURIComponent(pid) + '/advisories/' + advisoryId + '/acknowledge');
    if (d.ok) await loadAdvisories();
    else alert(d.message || 'Failed');
  }

  /* PRE-KICKOFF REVIEW (Sprint 2R) */

  async function loadReviewProjects() {
    var sel = document.getElementById('review-project-select');
    try {
      var d = await _api('GET', '/projects');
      if (!d.ok) return;
      sel.innerHTML = '<option value="">(select project)</option>' +
        (d.projects || []).map(function(p) {
          var badge = '';
          if (p.project_status === 'pre_kickoff_review') badge = ' — ✓ Ready for review';
          else if (p.project_status === 'kickoff_ready') badge = ' — 🔵 Kickoff ready';
          else if (p.project_status === 'review_rejected') badge = ' — ⚠ Revision needed';
          return '<option value="' + p.project_id + '">' + _esc(p.project_name) + badge + '</option>';
        }).join('');
    } catch(e) {}
  }

  // Sprint 2R: delegate clicks on review action buttons via data-action
  document.addEventListener('click', function(e) {
    var btn = e.target.closest('[data-action]');
    if (!btn) return;
    var pid = btn.dataset.pid;
    var reviewer = btn.dataset.reviewer;
    var action = btn.dataset.action;
    if (action === 'approve' || action === 'revision' || action === 'request') { doRecordOutcome(pid, reviewer, action); }
    else if (action === 'recommend_kickoff' || action === 'recommend_revision') { doRecommendKickoff(pid, action); }
  });

  async function doLoadReview() {
    var pid = document.getElementById('review-project-select').value;
    var out = document.getElementById('review-output');
    if (!pid) { _err(out, 'Select a project first.'); return; }
    _neutral(out, 'Loading...');
    try {
      var [revD, prereqD] = await Promise.all([
        _api('GET', '/projects/' + encodeURIComponent(pid) + '/review-status'),
        _api('GET', '/projects/' + encodeURIComponent(pid) + '/prerequisites'),
      ]);
      if (!revD.ok) { _err(out, revD.message || 'Failed to load review status.'); return; }
      _ok(out, 'Review status loaded');
      renderReviewCards(pid, revD, prereqD);
      document.getElementById('review-cards').style.display = '';
    } catch(e) {
      _err(out, 'Failed to load: ' + e.message);
    }
  }

  async function onReviewProjectChange() {
    document.getElementById('review-cards').style.display = 'none';
    document.getElementById('review-prereq-section').style.display = 'none';
    document.getElementById('review-output').innerHTML = '';
  }

  function renderReviewCards(pid, d, prereqD) {
    // Render prerequisite package (6/6)
    renderPrereqSection(prereqD);

    var rs = d.review_status;
    ['ba','sa','qa'].forEach(function(r) {
      document.getElementById('review-' + r + '-status').innerHTML = renderReviewerStatus(rs[r]);
      document.getElementById('review-' + r + '-actions').innerHTML = renderReviewerActions(pid, r, rs[r]);
    });
    var mav = rs.maverick_recommendation;
    document.getElementById('review-maverick-status').innerHTML = renderMaverickStatus(mav);
    document.getElementById('review-maverick-actions').innerHTML = renderMaverickActions(pid, mav, d.can_recommend_kickoff, d.any_revision_needed);
  }

  function renderPrereqSection(d) {
    var section = document.getElementById('review-prereq-section');
    var badge = document.getElementById('review-prereq-badge');
    var list = document.getElementById('review-prereq-list');
    if (!d || !d.ok) { section.style.display = 'none'; return; }

    var artifacts = d.artifacts || {};
    var submitted = d.prerequisite_submitted || 0;
    var complete = d.prerequisite_complete;
    badge.textContent = submitted + '/6 submitted';
    badge.className = 'badge ' + (complete ? 'badge-complete' : 'badge-missing');

    var typeInfo = {
      scope:     {label: 'Scope',         icon: '📐'},
      spec:      {label: 'Specification',  icon: '📄'},
      arch:      {label: 'Architecture',   icon: '🏗️'},
      testcase:  {label: 'Test Case',      icon: '🧪'},
      testreport:{label: 'Test Report',   icon: '📋'},
      guideline: {label: 'Guideline',      icon: '📏'},
    };

    list.innerHTML = '<div class="card"><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.75rem">' +
      Object.keys(typeInfo).map(function(t) {
        var info = typeInfo[t];
        var art = artifacts[t] || {};
        var done = art.submitted;
        var preview = art.content_preview || '';
        var producer = art.producer || '—';
        var at = art.submitted_at ? _ts(art.submitted_at) : '—';
        return '<div style="padding:0.5rem;border:1px solid var(--border-light);border-radius:6px">' +
          '<div style="display:flex;align-items:center;gap:0.3rem;margin-bottom:0.25rem">' +
          '<span style="font-size:0.9rem">' + info.icon + '</span>' +
          '<span style="font-size:0.8rem;font-weight:600">' + info.label + '</span>' +
          (done
            ? '<span class="badge badge-complete" style="margin-left:auto;font-size:0.6rem">✓</span>'
            : '<span class="badge badge-missing" style="margin-left:auto;font-size:0.6rem">○</span>') +
          '</div>' +
          (done
            ? '<div style="font-size:0.7rem;color:var(--text-dim);margin-bottom:0.2rem">By: ' + _esc(producer) + ' · ' + at + '</div>' +
              '<div style="font-size:0.7rem;color:var(--text-muted);line-height:1.3">' + _esc(preview.substring(0, 80)) + (preview.length > 80 ? '…' : '') + '</div>'
            : '<div style="font-size:0.7rem;color:var(--text-muted)">Not submitted</div>') +
          '</div>';
      }).join('') +
      '</div></div>';

    section.style.display = '';
  }

  function renderReviewerStatus(s) {
    var statusMap = {
      'pending': {cls: 'neutral', label: 'pending'},
      'approved': {cls: 'ok', label: 'approved'},
      'revision_needed': {cls: 'error', label: 'revision needed'}
    };
    var info = statusMap[s.status] || statusMap['pending'];
    var req = s.requested_at ? escHtml(s.requested_at.substring(0, 16)) : '---';
    var dec = s.decided_at ? escHtml(s.decided_at.substring(0, 16)) : '---';
    var note = s.note ? '<div style="font-size:0.8rem;color:var(--text-dim);margin-top:0.25rem">' + escHtml(s.note) + '</div>' : '';
    return '<div class="output ' + info.cls + '" style="margin:0">' + info.label + '</div>' +
      '<div style="font-size:0.75rem;color:var(--text-dim);margin-top:0.3rem">Requested: ' + req + '</div>' +
      '<div style="font-size:0.75rem;color:var(--text-dim)">Decided: ' + dec + '</div>' + note;
  }

  function renderReviewerActions(pid, reviewer, s) {
    if (s.status !== 'pending') return '';
    if (!s.requested_at) {
      return '<button class="primary sm" style="margin-top:0.5rem" data-pid="' + pid + '" data-reviewer="' + reviewer + '" data-action="request">Request</button>';
    }
    return '<button class="success sm" style="margin-top:0.5rem" data-pid="' + pid + '" data-reviewer="' + reviewer + '" data-action="approve">Approve</button>' +
      '<button class="danger sm" style="margin-top:0.25rem" data-pid="' + pid + '" data-reviewer="' + reviewer + '" data-action="revision">Revision</button>';
  }

  function renderMaverickStatus(mav) {
    var statusMap = {
      'pending': {cls: 'neutral', label: 'Pending -- awaiting all reviewer decisions'},
      'recommend_kickoff': {cls: 'ok', label: 'Recommend Kickoff'},
      'recommend_revision': {cls: 'error', label: 'Recommend Revision'}
    };
    var info = statusMap[mav.status] || statusMap['pending'];
    var when = mav.recommended_at ? escHtml(mav.recommended_at.substring(0, 16)) : '';
    var note = mav.note ? '<div style="font-size:0.8rem;color:var(--text-dim);margin-top:0.25rem">' + escHtml(mav.note) + '</div>' : '';
    return '<div class="output ' + info.cls + '" style="margin:0">' + info.label + '</div>' +
      (when ? '<div style="font-size:0.75rem;color:var(--text-dim);margin-top:0.3rem">When: ' + when + '</div>' : '') + note;
  }

  function renderMaverickActions(pid, mav, canRec, anyRevision) {
    if (mav.status !== 'pending') return '';
    if (canRec) {
      return '<div class="form-row" style="margin-top:0.5rem"><div class="field" style="flex:2"><textarea id="mav-note" rows="2" placeholder="Recommendation note (optional)"></textarea></div></div>' +
        '<div style="display:flex;gap:0.3rem;margin-top:0.3rem"><button class="success" data-pid="' + pid + '" data-action="recommend_kickoff">Recommend Kickoff</button><button class="secondary" data-pid="' + pid + '" data-action="recommend_revision"> Recommend Revision</button></div>';
    } else if (anyRevision) {
      return '<div style="font-size:0.8rem;color:var(--warning);margin-top:0.5rem">Complete all reviews with no revision needed first.</div>' +
        '<div style="margin-top:0.3rem"><button class="secondary" data-pid="' + pid + '" data-action="recommend_revision"> Recommend Revision</button></div>';
    } else {
      return '<div style="font-size:0.8rem;color:var(--text-dim);margin-top:0.5rem">Waiting for all reviews to complete.</div>';
    }
  }

  async function doRecordOutcome(pid, reviewer, action) {
    if (action === 'request') {
      var actor = prompt('Reviewer name:');
      if (!actor) return;
      var d = await _api('POST', '/projects/' + encodeURIComponent(pid) + '/reviews/' + reviewer + '/request', {actor: actor});
      if (d.ok) { await doLoadReview(); }
      else { alert(d.message || 'Failed'); }
    } else {
      var note = prompt('Decision note (optional):') || '';
      var actor = prompt('Reviewer name:');
      if (!actor) return;
      var d = await _api('POST', '/projects/' + encodeURIComponent(pid) + '/reviews/' + reviewer + '/outcome', {outcome: action, note: note, actor: actor});
      if (d.ok) { await doLoadReview(); }
      else { alert(d.message || 'Failed'); }
    }
  }
  async function doRecommendKickoff(pid, action) {
    var note = document.getElementById('mav-note') ? document.getElementById('mav-note').value : '';
    var actor = prompt('Your name (Maverick):');
    if (!actor) return;
    var d = await _api('POST', '/projects/' + encodeURIComponent(pid) + '/recommend-kickoff', {recommendation: action, note: note, actor: actor});
    if (d.ok) {
      await doLoadReview();
      alert('Recommendation recorded');
    } else {
      alert(d.message || d.error || 'Failed');
    }
  }



  



  
  /* ── WORKSPACE SHELL (Alpine.js) ── */
  document.addEventListener('alpine:init', () => {
    Alpine.data('workspaceShell', () => ({
      projectName: '', projectOwner: '', projectGoal: '', projectStatus: '',
      projectCreated: '', projectId: '',
      intakeSummary: '', intakeDeliverable: '', intakeContext: '',
      pipelineActive: false, currentStage: null,
      taskTotal: 0, taskDone: 0, taskBlocked: 0,
      lang: localStorage.getItem('pmo_lang') || 'en',
      T: {},

      init() {
        this.loadTranslations();
      },

      async loadTranslations() {
        if (window.T && window.T[this.lang]) {
          this.T = window.T[this.lang];
        }
      },

      t(key) { return this.T[key] || key; },

      async loadProjectData() {
        const pid = document.getElementById('global-project-select')?.value;
        if (!pid) return;
        this.projectId = pid;
        try {
          const projRes = await fetch(BASE + '/projects/' + encodeURIComponent(pid));
          const proj = await projRes.json();
          if (!proj.ok) return;
          this.projectName = proj.project_name || '';
          this.projectOwner = proj.project_owner || '';
          this.projectGoal = proj.project_goal || '';
          this.projectStatus = proj.project_status || '';
          this.projectCreated = proj.created_at || '';
          // Intake fields — clearly from submitted intake, NOT project state
          this.intakeSummary = proj.intake_summary || '';
          this.intakeDeliverable = proj.intake_deliverable || '';
          this.intakeContext = proj.intake_business_context || '';
          // Update DOM for manual rendering
          document.getElementById('ws-proj-name').textContent = this.projectName;
          document.getElementById('ws-proj-owner').textContent = this.projectOwner;
          document.getElementById('ws-proj-goal').textContent = this.projectGoal || '—';
          document.getElementById('ws-proj-status').innerHTML = '<span class="badge ' + this.badgeClass(this.projectStatus) + '">' + this.projectStatus + '</span>';
          document.getElementById('ws-proj-created').textContent = this.projectCreated ? new Date(this.projectCreated).toLocaleString() : '—';
          // Intake summary fields
          document.getElementById('ws-intake-summary-val').textContent = this.intakeSummary || '—';
          document.getElementById('ws-intake-deliverable-val').textContent = this.intakeDeliverable || '—';
          document.getElementById('ws-intake-context-val').textContent = this.intakeContext || '—';
          // Tasks for pipeline stage
          const tasksRes = await fetch(BASE + '/projects/' + encodeURIComponent(pid) + '/tasks');
          const tasksData = await tasksRes.json();
          if (tasksData.ok && tasksData.tasks && tasksData.tasks.length > 0) {
            this.taskTotal = tasksData.tasks.length;
            this.taskDone = tasksData.tasks.filter(t => t.task_status === 'done' || t.task_status === 'complete').length;
            this.taskBlocked = tasksData.tasks.filter(t => t.task_status === 'blocked').length;
            const activeTask = tasksData.tasks.find(t => t.task_status === 'in_progress');
            this.currentStage = activeTask?.current_stage || tasksData.tasks[0]?.current_stage || null;
            this.pipelineActive = !!this.currentStage;
            this.renderPipeline();
          } else {
            this.pipelineActive = false;
            this.renderPipeline();
          }
        } catch(e) {
          console.error('workspace load error', e);
        }
      },

      renderPipeline() {
        const el = document.getElementById('ws-pipeline');
        const note = document.getElementById('ws-pipeline-note');
        if (!el) return;
        if (!this.pipelineActive || !this.currentStage) {
          el.innerHTML = '<div class="pipeline-none">No active pipeline — project not yet started</div>';
          if (note) note.style.display = 'block';
          return;
        }
        if (note) note.style.display = 'none';
        const stages = [
          {k:'INTAKE', label:'Intake'}, {k:'BA', label:'BA'},
          {k:'SA', label:'SA'}, {k:'DEV', label:'Dev'},
          {k:'QA', label:'QA'}, {k:'DONE', label:'Done'},
        ];
        const currentIdx = stages.findIndex(s => s.k === this.currentStage);
        el.innerHTML = stages.map((s, i) => {
          let cls = '';
          if (i < currentIdx) cls = 'done';
          else if (i === currentIdx) cls = 'current';
          const icon = i < currentIdx ? '✓' : i === currentIdx ? '→' : '';
          return '<div class="pipeline-stage ' + cls + '">' +
            '<div class="pipeline-icon ' + cls + '">' + icon + '</div>' +
            '<div class="pipeline-label">' + s.label + '</div></div>' +
            (i < stages.length - 1 ? '<div class="pipeline-connector ' + (i < currentIdx ? 'done' : '') + '"></div>' : '');
        }).join('');
      },

      badgeClass(status) {
        const map = {active:'badge-active', on_hold:'badge-hold', closed:'badge-closed', shutdown:'badge-shutdown'};
        return map[status] || 'badge-closed';
      }
    }));
  })
  window.workspaceShell = Alpine.data("workspaceShell");
;

  /* ── INIT ── */
  loadGlobalProjects();
  intakeValidate();
/* ── INIT ── */
  loadGlobalProjects();
  intakeValidate();
  // Set nav active
  document.querySelectorAll('.nav-item')[0]?.classList.add('active');
