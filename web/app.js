const state = {
  step: 0,
  domains: [],
  selectedDomains: new Set(),
  customDomainOpen: false,
  perGroupTextMode: false,
};

const $ = (id) => document.getElementById(id);

let _toastTimer = null;

function showToast(msg, type = "error") {
  const el = $("toast");
  if (!el) return;
  if (_toastTimer) clearTimeout(_toastTimer);
  el.textContent = msg;
  el.className = `toast show ${type}`;
  _toastTimer = setTimeout(() => {
    el.classList.remove("show");
  }, 4500);
}

function escapeHtml(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

const CHAT_MESSAGES = [
  "<p><strong>Bonjour.</strong> Je suis RecruitAI, votre assistant de staffing associatif.</p><p>Question 1 : Quels domaines de votre evenement souhaitez-vous couvrir ?</p>",
  "<p>Parfait ! Combien de candidats souhaitez-vous par groupe de travail ?</p>",
  "<p>Analyse complete. Voici les groupes formes selon les profils de vos candidats.</p>",
];

function updateChat(step) {
  const body = $("chat-body");
  if (body && CHAT_MESSAGES[step]) {
    body.innerHTML = CHAT_MESSAGES[step];
  }
}

function setStep(step) {
  state.step = step;
  [$("step-0"), $("step-1"), $("step-2")].forEach((el, idx) => {
    el.classList.toggle("hidden", idx !== step);
  });

  const stepNodes = Array.from(document.querySelectorAll(".step"));
  const lineNodes = Array.from(document.querySelectorAll(".line"));

  stepNodes.forEach((el, idx) => {
    el.classList.remove("active", "done");
    if (idx < step) {
      el.classList.add("done");
      el.textContent = "✓";
    } else if (idx === step) {
      el.classList.add("active");
      el.textContent = String(idx + 1);
    } else {
      el.textContent = String(idx + 1);
    }
  });

  lineNodes.forEach((line, idx) => {
    line.classList.toggle("done", idx < step);
  });

  updateChat(step);
}

function renderDomainButtons() {
  const grid = $("domain-grid");
  grid.innerHTML = "";

  state.domains.forEach((domain) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "domain-btn";
    btn.style.setProperty("--c", domain.color);

    const isActive = state.selectedDomains.has(domain.label);
    if (isActive) btn.classList.add("active");

    btn.innerHTML = `<span class="domain-icon">${escapeHtml(domain.icon)}</span><span>${escapeHtml(domain.label)}</span>`;

    btn.addEventListener("click", () => {
      if (state.selectedDomains.has(domain.label)) {
        state.selectedDomains.delete(domain.label);
      } else {
        state.selectedDomains.add(domain.label);
      }
      renderDomainButtons();
      renderSelectedDomains();
    });

    grid.appendChild(btn);
  });
}

function renderSelectedDomains() {
  const container = $("selected-domains");
  const names = Array.from(state.selectedDomains);
  container.innerHTML = names
    .map((name) => `<span class="chip">${escapeHtml(name)}</span>`)
    .join("");
}

async function loadDomains() {
  const res = await fetch("/api/domains");
  if (!res.ok) throw new Error("Impossible de charger les domaines");
  const payload = await res.json();
  state.domains = payload.domains || [];
  renderDomainButtons();
}

function formatScore(score) {
  const val = parseFloat(score) || 0;
  if (val <= 0) return '<span class="score-badge score-none">—</span>';
  if (val < 1) {
    const pct = Math.round(val * 100);
    const cls = pct >= 70 ? "score-high" : pct >= 40 ? "score-med" : "score-low";
    return `<span class="score-badge ${cls}">${pct}%</span>`;
  }
  const cls = val >= 5 ? "score-high" : val >= 2 ? "score-med" : "score-low";
  return `<span class="score-badge ${cls}">${val.toFixed(0)} pts</span>`;
}

function renderStats(stats) {
  $("stats").innerHTML = `
    <div class="stat"><div class="v">${escapeHtml(stats.total_candidates)}</div><div class="l">Candidats analyses</div></div>
    <div class="stat"><div class="v">${escapeHtml(stats.group_count)}</div><div class="l">Groupes formes</div></div>
    <div class="stat"><div class="v">${escapeHtml(stats.max_per_group)}</div><div class="l">Max par groupe</div></div>
  `;
}

function renderErrors(errors) {
  const box = $("api-errors");
  if (!errors || !errors.length) { box.innerHTML = ""; return; }
  const lines = errors.map((e) => `<li>${escapeHtml(e)}</li>`).join("");
  box.innerHTML = `<div class="error-box"><strong>Fichiers non traites :</strong><ul>${lines}</ul></div>`;
}

const chartState = {
  allGroups: [],
  expandedIdx: null,
};

function renderDistributionChart(groups) {
  if (!groups || !groups.length) return;

  const svg = $("distribution-chart");
  const legendContainer = $("chart-legend");
  const totalEl = $("chart-total");
  if (!svg || !legendContainer || !totalEl) return;

  svg.innerHTML = "";
  legendContainer.innerHTML = "";

  const data = groups.map((g, idx) => ({
    idx: idx,
    domain: escapeHtml(g.domain),
    count: parseInt(g.count) || 0,
    color: g.color || "#7DD3FC",
    icon: g.icon || "●",
    candidates: (g.candidates || []).map((c) => ({
      name: escapeHtml(c.name || "Inconnu"),
      score: c.score,
      department: escapeHtml(c.department || ""),
    })),
  }));

  chartState.allGroups = data;

  const total = data.reduce((sum, d) => sum + d.count, 0);
  totalEl.textContent = total;

  if (total === 0) return;

  const cx = 200, cy = 200, radius = 140, innerRadius = 85;
  let currentAngle = -90;

  // Render donut slices
  data.forEach((d) => {
    const percentage = d.count / total;
    const sliceAngle = percentage * 360;
    const endAngle = currentAngle + sliceAngle;

    const startRad = (currentAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;

    const x1 = cx + radius * Math.cos(startRad);
    const y1 = cy + radius * Math.sin(startRad);
    const x2 = cx + radius * Math.cos(endRad);
    const y2 = cy + radius * Math.sin(endRad);

    const x3 = cx + innerRadius * Math.cos(endRad);
    const y3 = cy + innerRadius * Math.sin(endRad);
    const x4 = cx + innerRadius * Math.cos(startRad);
    const y4 = cy + innerRadius * Math.sin(startRad);

    const largeArc = sliceAngle > 180 ? 1 : 0;

    const pathData = [
      `M ${x1} ${y1}`,
      `A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`,
      `L ${x3} ${y3}`,
      `A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${x4} ${y4}`,
      `Z`,
    ].join(" ");

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", pathData);
    path.setAttribute("fill", d.color);
    path.setAttribute("stroke", "rgba(255,255,255,0.15)");
    path.setAttribute("stroke-width", "2");
    path.setAttribute("class", `donut-slice slice-${d.idx}`);
    path.setAttribute("data-idx", d.idx);
    path.style.transition = "all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)";
    path.style.cursor = "pointer";
    path.style.filter = "drop-shadow(0 8px 16px rgba(0,0,0,0.3))";

    path.addEventListener("mouseenter", () => {
      path.style.filter = "drop-shadow(0 12px 24px rgba(0,0,0,0.5))";
      const scaleOffset = 10;
      const midAngle = (startRad + endRad) / 2;
      const tx = scaleOffset * Math.cos(midAngle);
      const ty = scaleOffset * Math.sin(midAngle);
      path.style.transform = `translate(${tx}px, ${ty}px)`;

      document.querySelectorAll(".legend-item").forEach((item, i) => {
        item.style.opacity = i === d.idx ? "1" : "0.5";
      });
    });

    path.addEventListener("mouseleave", () => {
      path.style.filter = "drop-shadow(0 8px 16px rgba(0,0,0,0.3))";
      path.style.transform = "translate(0, 0)";

      document.querySelectorAll(".legend-item").forEach((item) => {
        item.style.opacity = "1";
      });
    });

    path.addEventListener("click", () => {
      expandChart(d);
    });

    svg.appendChild(path);

    const midAngle = (startRad + endRad) / 2;
    const labelRadius = (radius + innerRadius) / 2;
    const labelX = cx + labelRadius * Math.cos(midAngle);
    const labelY = cy + labelRadius * Math.sin(midAngle);
    const pct = Math.round(percentage * 100);

    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", labelX);
    text.setAttribute("y", labelY);
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("dominant-baseline", "middle");
    text.setAttribute("fill", "#fff");
    text.setAttribute("font-size", "14");
    text.setAttribute("font-weight", "700");
    text.setAttribute("pointer-events", "none");
    text.textContent = pct > 8 ? `${pct}%` : "";
    svg.appendChild(text);

    currentAngle = endAngle;
  });

  // Render legend
  const legend = document.createElement("div");
  legend.className = "chart-legend-grid";

  data.forEach((d) => {
    const pct = Math.round((d.count / total) * 100);
    const item = document.createElement("div");
    item.className = "legend-item";
    item.style.cursor = "pointer";
    item.innerHTML = `
      <div class="legend-color" style="background-color: ${d.color}"></div>
      <div class="legend-info">
        <div class="legend-domain">${d.domain}</div>
        <div class="legend-stat">${d.count} profil${d.count > 1 ? "s" : ""} • ${pct}%</div>
      </div>
    `;
    item.style.transition = "opacity 0.2s ease";
    item.addEventListener("click", () => {
      expandChart(d);
    });
    legend.appendChild(item);
  });

  legendContainer.appendChild(legend);
}

function expandChart(domainData) {
  chartState.expandedIdx = domainData.idx;

  const expandedView = $("expanded-view");
  const expandedCircle = $("expanded-circle");
  const expandedTitle = $("expanded-domain-title");
  const expandedNamesList = $("expanded-names-list");
  const expandedDomainHeader = $("expanded-domain-header");

  if (!expandedView || !expandedCircle || !expandedTitle || !expandedNamesList) return;

  // Set circle color and glow
  expandedCircle.setAttribute("fill", domainData.color);

  // Update title
  expandedTitle.textContent = domainData.domain;
  expandedTitle.style.color = domainData.color;

  // Render names list
  expandedNamesList.innerHTML = "";
  if (domainData.candidates && domainData.candidates.length > 0) {
    domainData.candidates.forEach((candidate, idx) => {
      const nameEl = document.createElement("div");
      nameEl.className = "expanded-name-item";
      nameEl.innerHTML = `
        <div class="name-avatar" style="background: linear-gradient(135deg, ${domainData.color}99 0%, ${domainData.color}66 100%);"></div>
        <div class="name-content">
          <div class="name-text">${candidate.name}</div>
          ${candidate.department ? `<div class="name-dept">${candidate.department}</div>` : ""}
        </div>
      `;
      nameEl.style.animationDelay = `${idx * 0.08}s`;
      expandedNamesList.appendChild(nameEl);
    });
  }

  // Show expanded view
  expandedView.classList.remove("hidden");
  setTimeout(() => {
    expandedView.classList.add("show");
  }, 10);
}

function collapseChart() {
  chartState.expandedIdx = null;
  const expandedView = $("expanded-view");

  if (!expandedView) return;

  expandedView.classList.remove("show");
  setTimeout(() => {
    expandedView.classList.add("hidden");
  }, 300);
}

function buildExplanation(candidate, domain) {
  const sentences = [];
  const name = escapeHtml(candidate.name || "Ce candidat");
  const dom = escapeHtml(domain);

  // Core reason: why this domain
  const kw = candidate.matched_kw && candidate.matched_kw.length > 0
    ? candidate.matched_kw
    : null;
  const skills = candidate.skills && candidate.skills.length > 0
    ? candidate.skills.slice(0, 3)
    : null;

  if (kw) {
    sentences.push(
      `${name} a été placé(e) dans le groupe <strong>${dom}</strong> car son CV reflète directement les besoins de ce domaine, notamment à travers les termes : <em>${escapeHtml(kw.join(", "))}</em>.`
    );
  } else if (skills) {
    sentences.push(
      `${name} a été placé(e) dans le groupe <strong>${dom}</strong> grâce à ses compétences en <em>${escapeHtml(skills.join(", "))}</em>, qui correspondent au profil recherché pour ce domaine.`
    );
  } else {
    sentences.push(
      `${name} a été placé(e) dans le groupe <strong>${dom}</strong> par correspondance sémantique avec les profils attendus dans ce domaine.`
    );
  }

  // Skills complement (only if keywords already opened)
  if (kw && skills) {
    sentences.push(
      `Ses compétences en <em>${escapeHtml(skills.join(", "))}</em> renforcent sa pertinence pour ce groupe.`
    );
  }

  // Education
  if (candidate.education && candidate.education !== "Not specified") {
    sentences.push(
      `Sa formation en <em>${escapeHtml(candidate.education)}</em> constitue un atout supplémentaire pour contribuer efficacement aux activités du domaine.`
    );
  }

  // Summary (AI-generated profile, skip auto-extraction noise)
  if (candidate.summary) {
    sentences.push(escapeHtml(candidate.summary));
  }

  // Experience
  const exp = parseInt(candidate.experience, 10);
  if (exp > 0) {
    sentences.push(
      `Avec ${exp} an${exp > 1 ? "s" : ""} d'expérience, ce profil apporte une maturité appréciable au sein du groupe.`
    );
  }

  if (sentences.length === 0) return "";

  return `<p class="expl-text">${sentences.join(" ")}</p>`;
}

function renderGroups(groups) {
  const root = $("groups");
  if (!groups || !groups.length) {
    root.innerHTML = "<p style='color:#94a3b8;text-align:center;padding:1rem'>Aucun CV trouve dans le dossier cvs.</p>";
    return;
  }

  root.innerHTML = groups
    .map((group) => {
      const border = `${group.color}66`;
      const soft = `${group.color}22`;
      const isUnclassified = /non clas/i.test(group.domain);

      const candidates = (group.candidates || [])
        .map((candidate) => {
          const skills = (candidate.skills || [])
            .map((s) => `<span class="tag">${escapeHtml(s)}</span>`)
            .join("");
          const explanation = buildExplanation(candidate, group.domain);

          return `
            <div class="candidate">
              <div class="candidate-header" role="button" tabindex="0" aria-expanded="false">
                <div class="candidate-header-left">
                  <div class="candidate-name">
                    ${escapeHtml(candidate.name || "Inconnu")}
                    <svg class="chevron" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <div class="candidate-meta">${escapeHtml(candidate.department || "General")}</div>
                </div>
                ${formatScore(candidate.score)}
              </div>
              <div class="expl-panel">
                ${explanation}
                ${skills ? `<div class="tag-row" style="padding:0 0 0.4rem">${skills}</div>` : ""}
              </div>
            </div>
          `;
        })
        .join("");

      return `
        <article class="group" style="--c-border:${border};--c-soft:${soft}">
          <div class="group-head">
            <div class="group-title">${escapeHtml(group.icon)} ${escapeHtml(group.domain)}</div>
            <div class="group-count">${escapeHtml(group.count)} profil${group.count > 1 ? "s" : ""}</div>
          </div>
          ${isUnclassified ? `<div class="group-summary">${escapeHtml(group.summary || "")}</div>` : ""}
          ${candidates}
        </article>
      `;
    })
    .join("");

  // Bind click-to-expand on every candidate header
  root.querySelectorAll(".candidate-header").forEach((header) => {
    const toggle = () => {
      const panel = header.nextElementSibling;
      const isOpen = header.getAttribute("aria-expanded") === "true";
      header.setAttribute("aria-expanded", String(!isOpen));
      panel.classList.toggle("open", !isOpen);
    };
    header.addEventListener("click", toggle);
    header.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); }
    });
  });
}

async function analyze() {
  const loading = $("loading");
  const analyzeBtn = $("analyze");

  setStep(2);
  $("stats").innerHTML = "";
  $("groups").innerHTML = "";
  $("api-errors").innerHTML = "";
  loading.classList.remove("hidden");
  analyzeBtn.disabled = true;

  const customDomain = state.customDomainOpen ? $("custom-domain").value.trim() : "";
  const perGroup = Number($("per-group").value || 3);
  const perGroupText = state.perGroupTextMode ? $("per-group-text").value.trim() : "";

  const body = {
    domains: Array.from(state.selectedDomains),
    custom_domain: customDomain || null,
    per_group: perGroup,
    per_group_text: perGroupText || null,
  };

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 120000);

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    const payload = await res.json();
    if (!res.ok) throw new Error(payload.detail || "Analyse impossible");

    renderStats(payload.stats || {});
    renderDistributionChart(payload.groups || []);
    renderErrors(payload.errors || []);
    renderGroups(payload.groups || []);
  } catch (err) {
    if (err.name === "AbortError") {
      showToast("Analyse trop longue (timeout). Verifiez le dossier cvs puis reessayez.", "error");
    } else {
      showToast(err.message || "Erreur inattendue", "error");
    }
    setStep(1);
  } finally {
    window.clearTimeout(timeoutId);
    loading.classList.add("hidden");
    analyzeBtn.disabled = false;
  }
}

function restartFlow() {
  state.step = 0;
  state.selectedDomains = new Set();
  state.customDomainOpen = false;
  state.perGroupTextMode = false;

  const expandedView = $("expanded-view");
  if (expandedView) expandedView.classList.add("hidden");
  chartState.expandedIdx = null;

  $("custom-domain").value = "";
  $("per-group").value = "3";
  $("per-group-text").value = "";

  $("custom-domain-wrap").classList.add("hidden");
  $("per-group-text-wrap").classList.add("hidden");

  renderDomainButtons();
  renderSelectedDomains();
  $("stats").innerHTML = "";
  $("groups").innerHTML = "";
  $("api-errors").innerHTML = "";
  $("distribution-chart").innerHTML = "";
  $("chart-legend").innerHTML = "";
  $("chart-total").textContent = "0";

  setStep(0);
}

function bindUi() {
  $("toggle-custom-domain").addEventListener("click", () => {
    state.customDomainOpen = !state.customDomainOpen;
    $("custom-domain-wrap").classList.toggle("hidden", !state.customDomainOpen);
    $("toggle-custom-domain").textContent = state.customDomainOpen ? "— Annuler" : "+ Autre domaine";
  });

  $("toggle-per-group-text").addEventListener("click", () => {
    state.perGroupTextMode = !state.perGroupTextMode;
    $("per-group-text-wrap").classList.toggle("hidden", !state.perGroupTextMode);
    $("toggle-per-group-text").textContent = state.perGroupTextMode ? "Annuler" : "Texte libre";
  });

  $("to-step-1").addEventListener("click", () => {
    const custom = state.customDomainOpen ? $("custom-domain").value.trim() : "";
    if (state.selectedDomains.size === 0 && !custom) {
      showToast("Selectionnez au moins un domaine", "warn");
      return;
    }
    setStep(1);
  });

  $("back-step-0").addEventListener("click", () => setStep(0));
  $("analyze").addEventListener("click", analyze);
  $("restart").addEventListener("click", restartFlow);

  // Expanded view controls
  const expandedCloseBtn = $("expanded-close-btn");
  const expandedView = $("expanded-view");
  if (expandedCloseBtn) expandedCloseBtn.addEventListener("click", collapseChart);
  if (expandedView) {
    expandedView.addEventListener("click", (e) => {
      if (e.target === expandedView) collapseChart();
    });
  }
}

function startBackgroundAnimation() {
  const canvas = $("bg-canvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d", { alpha: true });
  let w = 0, h = 0, pts = [];
  const colors = ["#64DCFF", "#7DD3FC", "#67E8F9", "#A5B4FC"];
  const mouse = { x: -9999, y: -9999 };

  function rand(a, b) { return a + Math.random() * (b - a); }
  function rgb(hex) {
    return `${parseInt(hex.slice(1,3),16)},${parseInt(hex.slice(3,5),16)},${parseInt(hex.slice(5,7),16)}`;
  }

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
    const n = w < 760 ? 50 : 100;
    pts = [];
    for (let i = 0; i < n; i++) {
      pts.push({ x: rand(0,w), y: rand(0,h), vx: rand(-0.3,0.3), vy: rand(-0.3,0.3),
        r: rand(0.5,2.0), c: colors[Math.floor(Math.random()*colors.length)], o: rand(0.45,0.85) });
    }
  }

  function draw() {
    ctx.clearRect(0, 0, w, h);
    for (let i = 0; i < pts.length; i++) {
      const p = pts[i];
      for (let j = i+1; j < pts.length; j++) {
        const q = pts[j];
        const d = Math.hypot(p.x-q.x, p.y-q.y);
        if (d < 140) {
          ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y);
          ctx.strokeStyle = `rgba(0,200,255,${(1-d/140)*0.24})`; ctx.lineWidth=1; ctx.stroke();
        }
      }
      const md = Math.hypot(p.x-mouse.x, p.y-mouse.y);
      if (md < 170 && md > 0) {
        ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(mouse.x,mouse.y);
        ctx.strokeStyle = `rgba(100,220,255,${(1-md/170)*0.26})`; ctx.lineWidth=1; ctx.stroke();
      }
      ctx.shadowBlur=8; ctx.shadowColor=p.c;
      ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle = `rgba(${rgb(p.c)},${p.o})`; ctx.fill();
      ctx.shadowBlur=0;
      p.vx += (Math.random()-0.5)*0.02; p.vy += (Math.random()-0.5)*0.02;
      p.vx *= 0.984; p.vy *= 0.984;
      const speed = Math.hypot(p.vx,p.vy);
      if (speed>1.6) { p.vx=(p.vx/speed)*1.6; p.vy=(p.vy/speed)*1.6; }
      p.x+=p.vx; p.y+=p.vy;
      if (p.x<-10) p.x=w+10; if (p.x>w+10) p.x=-10;
      if (p.y<-10) p.y=h+10; if (p.y>h+10) p.y=-10;
    }
    window.requestAnimationFrame(draw);
  }

  window.addEventListener("resize", resize);
  window.addEventListener("mousemove", (e) => { mouse.x=e.clientX; mouse.y=e.clientY; });
  window.addEventListener("mouseleave", () => { mouse.x=-9999; mouse.y=-9999; });
  resize(); draw();
}

async function init() {
  bindUi();
  setStep(0);
  startBackgroundAnimation();
  try {
    await loadDomains();
  } catch (err) {
    showToast(err.message || "Erreur chargement domaines", "error");
  }
}

window.addEventListener("DOMContentLoaded", init);
