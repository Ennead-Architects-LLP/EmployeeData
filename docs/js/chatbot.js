(function(){
	const apiBase = (window.CHAT_API_BASE || 'http://localhost:8000');

	function createWidget(){
		const btn = document.createElement('button');
		btn.textContent = '💬 Ask';
		btn.style.position = 'fixed';
		btn.style.right = '16px';
		btn.style.bottom = '16px';
		btn.style.zIndex = '9999';
		btn.style.padding = '10px 14px';
		btn.style.background = '#00bfff';
		btn.style.color = '#111';
		btn.style.border = 'none';
		btn.style.borderRadius = '20px';
		btn.style.cursor = 'pointer';

		const panel = document.createElement('div');
		panel.style.position = 'fixed';
		panel.style.right = '16px';
		panel.style.bottom = '60px';
		panel.style.width = '320px';
		panel.style.maxHeight = '50vh';
		panel.style.display = 'none';
		panel.style.flexDirection = 'column';
		panel.style.background = 'rgba(0,0,0,0.85)';
		panel.style.backdropFilter = 'blur(6px)';
		panel.style.border = '1px solid rgba(255,255,255,0.1)';
		panel.style.borderRadius = '8px';
		panel.style.padding = '10px';
		panel.style.zIndex = '9999';

		const log = document.createElement('div');
		log.style.overflow = 'auto';
		log.style.flex = '1';
		log.style.fontSize = '13px';
		log.style.color = '#e5e5e5';
		log.style.marginBottom = '8px';

		const input = document.createElement('input');
		input.type = 'text';
		input.placeholder = 'Ask about employees...';
		input.style.width = '100%';
		input.style.padding = '8px';
		input.style.borderRadius = '6px';
		input.style.border = '1px solid rgba(255,255,255,0.15)';
		input.style.background = 'rgba(255,255,255,0.06)';
		input.style.color = '#f0f0f0';

		panel.appendChild(log);
		panel.appendChild(input);
		document.body.appendChild(panel);
		document.body.appendChild(btn);

		btn.addEventListener('click', ()=>{
			panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
			if(panel.style.display === 'flex') input.focus();
		});

		input.addEventListener('keydown', async (e)=>{
			if(e.key !== 'Enter') return;
			const q = input.value.trim();
			if(!q) return;
			input.value = '';
			const you = document.createElement('div');
			you.textContent = 'You: ' + q;
			you.style.color = '#9be9a8';
			log.appendChild(you);
			log.scrollTop = log.scrollHeight;
			try{
				const url = apiBase + '/ask?q=' + encodeURIComponent(q);
				const res = await fetch(url);
				if(!res.ok) throw new Error('API error ' + res.status);
				const data = await res.json();
				const bot = document.createElement('div');
				bot.textContent = 'Bot: ' + (data.answer || '(no answer)');
				log.appendChild(bot);
				log.scrollTop = log.scrollHeight;
			}catch(err){
				const errDiv = document.createElement('div');
				errDiv.textContent = 'Error: ' + err.message;
				errDiv.style.color = '#ff8a8a';
				log.appendChild(errDiv);
				log.scrollTop = log.scrollHeight;
			}
		});
	}

	if(document.readyState === 'loading'){
		document.addEventListener('DOMContentLoaded', createWidget);
	}else{
		createWidget();
	}
})();
