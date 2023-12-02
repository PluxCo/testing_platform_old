let delayed = [false, false];

let timeline_labels = [];
let timeline_values_ignored = [];
let timeline_values_correct = [];
let timeline_values_incorrect = [];

for (const timelineKey of config.timeline) {
    timeline_labels.push(timelineKey[0])
    timeline_values_correct.push(timelineKey[1])
    timeline_values_incorrect.push(timelineKey[2])
    timeline_values_ignored.push(timelineKey[3])
}

let dataset = [];
for (let i = 0; i < config.bar_data[2]; i++) {
    const a = {
        type: 'bar',
        label: 'Level ' + (i + 1).toString(),
        data: config.bar_data[1][i],
        backgroundColor: colorize_bars((i - 1) / (config.bar_data[2] - 1)),
    }
    dataset.push(Object.create(a))
}

function colorize_bars(heat) {
    const first_color = [253, 200, 48];
    const second_color = [243, 115, 53];
    const r = first_color[0] + heat * (second_color[0] - first_color[0]);
    const g = first_color[1] + heat * (second_color[1] - first_color[1]);
    const b = first_color[2] + heat * (second_color[2] - first_color[2]);
    const a = 1;

    return 'rgba(' + r + ',' + g + ',' + b + ',' + a + ')';
}

new Chart(
    document.getElementById('QuestionChart'),
    {
        data: {
            labels: config.bar_data[0],
            datasets: dataset,
        },
        options: {
            locale: 'en-US',
            maintainAspectRatio: false,
            scales: {
                y: {
                    grid: {
                        display: true,
                        color: "rgba(104,157,61,0.2)"
                    },
                    ticks: {
                        callback: (value, index, values) => {
                            return `${value} %`
                        }
                    },
                    grace: '5%',
                },
                x: {
                    grid: {
                        display: false
                    },
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += `${context.parsed.y} %`;
                            }
                            return label;
                        }
                    }
                }
            },
            animation: {
                onComplete: () => {
                    delayed[0] = true;
                },
                delay: (context) => {
                    let delay = 0;
                    if (context.type === 'data' && context.mode === 'default' && !delayed[0]) {
                        delay = context.dataIndex * 300 + context.datasetIndex * 100;
                    }
                    return delay;
                },
            }
        }
    }
);

new Chart(
    document.getElementById('Timeline'),
    {
        data: {
            labels: timeline_labels,
            datasets: [
                {
                    type: 'line',
                    label: 'Ignored',
                    data: timeline_values_ignored,
                    backgroundColor: "rgba(176,176,176,0.2)",
                    borderColor: "rgb(194,194,194)",
                    hoverBackgroundColor: "rgba(185,185,185,0.4)",
                    hoverBorderColor: "rgb(180,180,180)",
                },
                {
                    type: 'line',
                    label: 'Correct',
                    data: timeline_values_correct,
                    backgroundColor: "rgba(123,185,72,0.2)",
                    borderColor: "rgb(122,204,81)",
                    hoverBackgroundColor: "rgba(138,196,76,0.4)",
                    hoverBorderColor: "rgb(136,187,73)",
                },
                {
                    type: 'line',
                    label: 'Incorrect',
                    data: timeline_values_incorrect,
                    backgroundColor: "rgba(185,72,72,0.2)",
                    borderColor: "rgb(204,81,81)",
                    hoverBackgroundColor: "rgba(196,76,76,0.4)",
                    hoverBorderColor: "rgb(187,73,73)",
                }
            ]
        },
        options: {
            locale: 'en-US',
            maintainAspectRatio: false,
            elements: {
                point: {
                    pointStyle: false
                }
            },
            scales: {
                x: {
                    type: 'time',
                    grid: {
                        display: true,
                        color: "rgba(104,157,61,0.2)",
                    },
                    ticks: {
                        maxTicksLimit: 6,
                    }
                },
                y: {
                    stacked: false,
                    grid: {
                        display: true,
                        color: "rgba(104,157,61,0.2)",
                    },
                    beginAtZero: true,
                    grace: '40%'
                }
            }
        }
    }
);

let heatmap_grid = [];
let heatmap_data = [];

for (let i = 0; i < config.bar_data[0].length; i++) {
    heatmap_data.push([]);
    for (let j = 0; j < config.bar_data[2]; j++) {
        heatmap_grid.push([i, j]);
        heatmap_data[i].push(config.bar_data[1][j][i]);
    }
}

function interpolate(x, y, z, t) {
    const a = 2 * z - 4 * y + 2 * x;
    const b = 4 * y - z - 3 * x;

    return a * t * t + b * t + x;
}

function colorize_heatmap(opaque, context) {
    const value = context.raw;
    const x = value[0];
    const y = value[1];
    const heat = heatmap_data[x][y] / 100;
    const orange = [220, 227, 91];
    const green = [69, 182, 73];
    const rose = [239, 59, 54];
    const r = interpolate(rose[0], orange[0], green[0], heat);
    const g = interpolate(rose[1], orange[1], green[1], heat);
    const b = interpolate(rose[2], orange[2], green[2], heat);
    // const r = first_color[0] + heat * (second_color[0] - first_color[0]);
    // const g = first_color[1] + heat * (second_color[1] - first_color[1]);
    // const b = first_color[2] + heat * (second_color[2] - first_color[2]);

    const a = 0.8;

    return 'rgba(' + r + ',' + g + ',' + b + ',' + a + ')';
}

new Chart(document.getElementById('Heatmap'), {
    type: 'matrix',
    data: {
        datasets: [{
            data: heatmap_grid,
            width: ({chart}) => (chart.chartArea || {}).width / (config.bar_data[0].length + 1) - 1,
            height: ({chart}) => (chart.chartArea || {}).height / (config.bar_data[2] + 1) - 1,
        }]
    },
    options: {
        maintainAspectRatio: false,
        scales: {
            x: {
                ticks: {
                    callback: function (val, index) {
                        return config.bar_data[0][val];
                    },
                },
                grid: {
                    display: false,
                    offset: false
                },
                min: -1,
                max: config.bar_data[0].length,
                offset: false
            },
            y: {
                reverse: false,
                grid: {
                    display: false
                },
                ticks: {
                    callback: function (val, index) {
                        if (val > -1 && val < config.bar_data[2]) {
                            return 'Level ' + (val + 1);
                        }
                    },
                    maxTicksLimit: config.bar_data[2] + 2
                },
                min: -1,
                max: config.bar_data[2],
            }
        },
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                callbacks: {
                    title: function (context) {
                        let title = '';
                        title += 'Level ' + (context[0].parsed.y + 1) + ' ' + config.bar_data[0][context[0].parsed.x];
                        return title;
                    },
                    label: function (context) {
                        let label = '';
                        if (context.parsed.y !== null) {
                            label += config.bar_data[1][context.parsed.y][context.parsed.x] + '%';
                        }
                        return label;
                    }
                }
            },
        },
        elements: {
            matrix: {
                backgroundColor: colorize_heatmap.bind(null, false),
                borderColor: colorize_heatmap.bind(null, true),
            }
        },
        animation: {
            onComplete: (context) => {
                if (context.type === 'data' && context.mode === 'attach') {
                    delayed[1] = true;
                }
            },
            delay: (context) => {
                let delay = 0;
                if (context.type === 'data' && context.mode === 'attach' && !delayed[1]) {
                    delay = context.dataIndex * 30 + context.datasetIndex * 10;
                    return delay;
                }
            }
        }
    }
});