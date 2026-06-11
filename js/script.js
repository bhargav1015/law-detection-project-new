// Determine API base URL. Defaults to local backend at 127.0.0.1:5000.
function getApiBase() {
	const params = new URLSearchParams(window.location.search);
	const override = params.get('backend');
	if (override) return override;
	if (typeof window.__API_BASE__ === 'string' && window.__API_BASE__) return window.__API_BASE__;
	if (location.protocol === 'file:') return 'http://127.0.0.1:5000';
	// Default to local backend port 5000 even when served from http server
	return 'http://127.0.0.1:5000';
}


async function analyzeCase() {
	const API_BASE = getApiBase();
	let text = document.getElementById("caseText").value.trim();
	let filesInput = document.getElementById("caseFiles");
	let errorDiv = document.getElementById("inputError");
	if (errorDiv) errorDiv.innerHTML = "";
	// Validation: require case description
	if (!text) {
		if (errorDiv) errorDiv.innerHTML = '<div class="alert alert-danger">Case description is required.</div>';
		else alert("Case description is required.");
		return;
	}
	// Optional: limit file size (e.g., 5MB per file)
	if (filesInput && filesInput.files.length > 0) {
		for (let i = 0; i < filesInput.files.length; i++) {
			if (filesInput.files[i].size > 5 * 1024 * 1024) {
				if (errorDiv) errorDiv.innerHTML = '<div class="alert alert-danger">Each file must be less than 5MB.</div>';
				else alert("Each file must be less than 5MB.");
				return;
			}
		}
	}
	let formData = new FormData();
	formData.append("caseText", text);
	if (filesInput && filesInput.files.length > 0) {
		for (let i = 0; i < filesInput.files.length; i++) {
			formData.append("files", filesInput.files[i]);
		}
	}
	// Check backend health before sending request
	const controller = new AbortController();
	const healthTimeout = setTimeout(() => controller.abort(), 3000);
	try {
		const h = await fetch(`${API_BASE}/health`, { signal: controller.signal });
		clearTimeout(healthTimeout);
		if (!h.ok) throw new Error('Backend health check failed');
	} catch (healthErr) {
		if (errorDiv) errorDiv.innerHTML = `<div class="alert alert-danger">Cannot reach backend at ${API_BASE} — start the backend: <code>backend\\venv\\Scripts\\activate &amp;&amp; python backend\\app.py</code></div>`;
		else alert(`Cannot reach backend at ${API_BASE}. Start the backend and try again.`);
		return;
	}
	try {
		const response = await fetch(`${API_BASE}/analyze`, {
			method: "POST",
			body: formData
		});
		if (!response.ok) {
			const errData = await response.json();
			throw new Error(errData.error || "API error");
		}
		const result = await response.json();
		localStorage.setItem("caseResult", JSON.stringify(result));
		window.location.href = "results.html";
	} catch (err) {
		if (errorDiv) errorDiv.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
		else alert("Failed to analyze case. " + err.message);
	}
}

// History page logic
async function loadHistory() {
	const container = document.getElementById("historyContainer");
	if (!container) return;
	try {
		const API_BASE = getApiBase();
		const res = await fetch(`${API_BASE}/history`);
		const history = await res.json();
		if (history.length === 0) {
			container.innerHTML = '<div class="alert alert-info">No previous analyses found.</div>';
			return;
		}
		let html = '<ul class="list-group">';
		history.forEach(item => {
			const viewedBadge = item.viewed ? `<span class="badge bg-success ms-2">Viewed</span>` : '';
			html += `<li class="list-group-item">
				<strong>Case #${item.id}:</strong> ${item.caseText.substring(0, 60)}...<br>
				<span class="badge bg-secondary">${item.category}</span>${viewedBadge}
				<button class="btn btn-sm btn-danger float-end ms-2" onclick="deleteAnalysis(${item.id})">Remove</button>
				<button class="btn btn-sm btn-primary float-end" onclick='viewAnalysis(${JSON.stringify(item)})'>View</button>
			</li>`;
		});
		html += '</ul>';
		container.innerHTML = html;
	} catch (e) {
		container.innerHTML = '<div class="alert alert-danger">Failed to load history.</div>';
	}
}

async function viewAnalysis(item) {
	const API_BASE = getApiBase();
	try {
		if (item && item.id) {
			// notify backend that this entry was viewed
			await fetch(`${API_BASE}/history/${item.id}/view`, { method: 'POST' });
			item.viewed = true;
		}
	} catch (e) {
		// non-fatal: continue to show the result even if marking viewed fails
		console.warn('Failed to mark viewed:', e);
	}
	localStorage.setItem("caseResult", JSON.stringify(item));
	window.location.href = "results.html";
}

async function deleteAnalysis(id) {
	if (!confirm("Are you sure you want to remove this analysis?")) return;
	const API_BASE = getApiBase();
	await fetch(`${API_BASE}/history/${id}`, { method: "DELETE" });
	loadHistory();
}


function filterLaw() {
	let input = document.getElementById("searchLaw").value.toLowerCase();
	let laws = document.querySelectorAll("#laws li");
	laws.forEach(function(item) {
		if (item.innerText.toLowerCase().includes(input)) {
			item.style.display = "block";
		} else {
			item.style.display = "none";
		}
	});
}

// Populate results.html with dynamic data
function populateResults() {
	const data = localStorage.getItem("caseResult");
	if (!data) return;
	const result = JSON.parse(data);
	// Category
	const catSpan = document.getElementById("caseCategory");
	if (catSpan) catSpan.textContent = result.category;
	// Laws
	const lawsUl = document.getElementById("laws");
	if (lawsUl && result.laws) {
		lawsUl.innerHTML = "";
		result.laws.forEach(law => {
			const li = document.createElement("li");
			li.innerHTML = `<i class='fa-solid fa-scale-balanced'></i> ${law.code} – ${law.desc}`;
			lawsUl.appendChild(li);
		});
	}
	// Defenses
	const defUl = document.getElementById("defense");
	if (defUl && result.defenses) {
		defUl.innerHTML = "";
		result.defenses.forEach(def => {
			const li = document.createElement("li");
			li.innerHTML = `<i class='fa-solid fa-shield'></i> ${def}`;
			defUl.appendChild(li);
		});
	}
	// Reasons
	const reasonsCard = document.getElementById('reasonsCard');
	const reasonsList = document.getElementById('reasonsList');
	if (reasonsList && result.reasons && Object.keys(result.reasons).length>0) {
		reasonsList.innerHTML = '';
		for (const code in result.reasons) {
			const li = document.createElement('li');
			li.textContent = `${code}: ${result.reasons[code]}`;
			reasonsList.appendChild(li);
		}
		if (reasonsCard) reasonsCard.style.display = 'block';
	} else if (reasonsCard) {
		reasonsCard.style.display = 'none';
	}
	// Follow-ups
	const followUpsCard = document.getElementById('followUpsCard');
	const followUpsDiv = document.getElementById('followUps');
	if (followUpsDiv && result.followUps && result.followUps.length>0) {
		followUpsDiv.innerHTML = '';
		result.followUps.forEach((q, idx) => {
			const wrapper = document.createElement('div');
			wrapper.className = 'mb-2';
			const label = document.createElement('label');
			label.className = 'form-label';
			label.textContent = q;
			const input = document.createElement('input');
			input.className = 'form-control';
			input.id = `followup_${idx}`;
			// Pre-fill with existing answer if present
			if (result.followUpAnswers && result.followUpAnswers[idx]) {
				input.value = result.followUpAnswers[idx].answer || '';
			}
			wrapper.appendChild(label);
			wrapper.appendChild(input);
			followUpsDiv.appendChild(wrapper);
		});
		if (followUpsCard) followUpsCard.style.display = 'block';
	} else if (followUpsCard) {
		followUpsCard.style.display = 'none';
	}
}

// Collect follow-up answers and re-run analysis by appending answers to case text
async function refineAnalysis() {
	const data = localStorage.getItem('caseResult');
	if (!data) return;
	const result = JSON.parse(data);
	const originalText = result.caseText || '';
	// collect answers
	const answers = [];
	if (result.followUps) {
		result.followUps.forEach((q, idx) => {
			const el = document.getElementById(`followup_${idx}`);
			const ans = el ? el.value.trim() : '';
			answers.push({ question: q, answer: ans });
		});
	}
	// send to backend with structured follow-up answers
	try {
		const formData = new FormData();
		formData.append('caseText', originalText);
		formData.append('followUpAnswers', JSON.stringify(answers));
		const API_BASE = getApiBase();
		const response = await fetch(`${API_BASE}/analyze`, { method: 'POST', body: formData });
		if (!response.ok) {
			const err = await response.json();
			throw new Error(err.error || 'API error');
		}
		const newResult = await response.json();
		localStorage.setItem('caseResult', JSON.stringify(newResult));
		populateResults();
		alert('Analysis refined and updated.');
	} catch (e) {
		alert('Failed to refine analysis: ' + e.message);
	}
}
