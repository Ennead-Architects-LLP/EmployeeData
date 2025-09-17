// Load employees and build charts of computer specs
(async function () {
    try {
        const url = (function buildEmployeesUrl() {
            const { protocol, hostname, pathname } = window.location;
            if (protocol === 'file:') return 'assets/employees.json';
            if (hostname.includes('github.io')) {
                const parts = pathname.split('/').filter(Boolean);
                const repo = parts[0] || 'EmployeeData';
                return `/${repo}/assets/employees.json`;
            }
            return 'assets/employees.json';
        })();

        const res = await fetch(url, { cache: 'no-store' });
        const data = await res.json();
        const employees = Array.isArray(data) ? data : Object.values(data);

        const computers = [];
        for (const emp of employees) {
            const info = emp.computer_info || emp.computer || emp.computer_specs;
            if (!info) continue;
            const items = Array.isArray(info) ? info : Object.values(info);
            for (const c of items) { computers.push(c); }
        }

        const fields = [
            { key: 'os', label: 'Operating System', altKey: 'OS' },
            { key: 'cpu', label: 'CPU', altKey: 'CPU' },
            { key: 'gpu_name', label: 'GPU', altKey: 'GPU Name' },
            { key: 'gpu_processor', label: 'GPU Processor', altKey: 'GPU Processor' },
            { key: 'manufacturer', label: 'Manufacturer', altKey: 'Manufacturer' },
            { key: 'model', label: 'Model', altKey: 'Model' },
                    { key: 'memory_bytes', label: 'RAM (GB)', altKey: 'Total Physical Memory', transform: v => v ? `${Math.round(Number(v) / (1024 * 1024 * 1024) * 10) / 10} GB` : undefined },
        ];

        const chartsContainer = document.getElementById('charts');

        for (const field of fields) {
            const counts = new Map();
            for (const c of computers) {
                // Try both lowercase and title case keys
                let value = c[field.key] || c[field.altKey];
                if (field.transform) value = field.transform(value);
                if (!value) continue;
                counts.set(value, (counts.get(value) || 0) + 1);
            }
            if (counts.size === 0) continue;

            const card = document.createElement('div');
            card.className = 'chart-card';
            card.innerHTML = `<h3>${field.label}</h3><canvas></canvas>`;
            chartsContainer.appendChild(card);

            const labels = Array.from(counts.keys()).sort((a,b)=>String(a).localeCompare(String(b)));
            const values = labels.map(l => counts.get(l));
            const total = values.reduce((a,b)=>a+b, 0);

            // Calm, desaturated professional palette (muted blues/teals/grays)
            function buildMutedPalette(size) {
                const base = [
                    '#6B8BA4', // muted steel blue
                    '#7FA7B3', // soft teal-blue
                    '#98B7C2', // light blue-gray
                    '#A9C3CA', // pale teal-gray
                    '#BDC8D6', // cool gray-blue
                    '#8A99A6', // slate gray-blue
                    '#7C9FA1', // desaturated teal
                    '#9FB1B5', // light slate teal
                    '#C2C9CF', // light gray
                    '#B1C7BC', // muted mint-gray
                ];
                const colors = [];
                for (let i = 0; i < size; i++) {
                    colors.push(base[i % base.length]);
                }
                return colors;
            }
            const colors = buildMutedPalette(labels.length);
            const borderColors = colors.map(c => c);

            const ctx = card.querySelector('canvas').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels,
                    datasets: [{
                        data: values,
                        backgroundColor: colors,
                        borderColor: borderColors,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#e5e5e5' } },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => {
                                    const count = ctx.parsed;
                                    const pct = total ? Math.round((count / total) * 1000) / 10 : 0;
                                    const name = ctx.label || '';
                                    return `${name}: ${count} (${pct}%)`;
                                }
                            }
                        },
                        title: { display: false }
                    },
                    cutout: '55%'
                }
            });
        }
    } catch (e) {
        const charts = document.getElementById('charts');
        if (charts) charts.innerHTML = `<div class="error-message">Failed to build charts: ${e?.message || e}</div>`;
        console.error(e);
    }
})();


