(function(){
	const REPO_OWNER = 'Ennead-Architects-LLP';
	const REPO_NAME = 'EmployeeData';
	const TRIGGER_LABEL = 'assistant-trigger';
	const POLL_INTERVAL = 3000; // 3 seconds
	const MAX_POLLS = 20; // 1 minute max

	let currentIssueNumber = null;
	let pollCount = 0;
	let pollInterval = null;

	function createTriggerIssue(question) {
		const title = `[Assistant] ${question.substring(0, 50)}${question.length > 50 ? '...' : ''}`;
		const body = `/ask ${question}\n\n(Triggered from website - will auto-close)`;
		
		return fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/issues`, {
			method: 'POST',
			headers: {
				'Accept': 'application/vnd.github.v3+json',
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				title: title,
				body: body,
				labels: [TRIGGER_LABEL]
			})
		}).then(res => {
			if (!res.ok) throw new Error(`GitHub API error: ${res.status}`);
			return res.json();
		});
	}

	function pollForResponse(issueNumber) {
		return fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/issues/${issueNumber}/comments`, {
			headers: {
				'Accept': 'application/vnd.github.v3+json'
			}
		}).then(res => {
			if (!res.ok) throw new Error(`GitHub API error: ${res.status}`);
			return res.json();
		});
	}

	function closeIssue(issueNumber) {
		return fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/issues/${issueNumber}`, {
			method: 'PATCH',
			headers: {
				'Accept': 'application/vnd.github.v3+json',
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				state: 'closed'
			})
		});
	}

	function extractAnswerFromComment(comment) {
		// Look for the bot's response after "🤖 Assistant reply:"
		const lines = comment.body.split('\n');
		let inAnswer = false;
		let answerLines = [];
		
		for (const line of lines) {
			if (line.includes('🤖 Assistant reply:')) {
				inAnswer = true;
				continue;
			}
			if (inAnswer) {
				if (line.trim() === '') break;
				answerLines.push(line);
			}
		}
		
		return answerLines.join('\n').trim();
	}

	function startPolling(issueNumber, onAnswer, onError) {
		currentIssueNumber = issueNumber;
		pollCount = 0;
		
		pollInterval = setInterval(async () => {
			try {
				pollCount++;
				const comments = await pollForResponse(issueNumber);
				
				// Look for bot response
				for (const comment of comments) {
					if (comment.body.includes('🤖 Assistant reply:')) {
						const answer = extractAnswerFromComment(comment);
						if (answer) {
							clearInterval(pollInterval);
							onAnswer(answer);
							// Close the issue
							closeIssue(issueNumber).catch(console.error);
							return;
						}
					}
				}
				
				// Timeout after max polls
				if (pollCount >= MAX_POLLS) {
					clearInterval(pollInterval);
					onError('Timeout waiting for response');
					closeIssue(issueNumber).catch(console.error);
				}
			} catch (err) {
				clearInterval(pollInterval);
				onError(err.message);
			}
		}, POLL_INTERVAL);
	}

	function stopPolling() {
		if (pollInterval) {
			clearInterval(pollInterval);
			pollInterval = null;
		}
		if (currentIssueNumber) {
			closeIssue(issueNumber).catch(console.error);
			currentIssueNumber = null;
		}
	}

	// Export functions
	window.GitHubAssistant = {
		askQuestion: async function(question, onAnswer, onError) {
			try {
				stopPolling(); // Stop any existing polling
				const issue = await createTriggerIssue(question);
				startPolling(issue.number, onAnswer, onError);
			} catch (err) {
				onError(err.message);
			}
		},
		stopPolling: stopPolling
	};
})();
