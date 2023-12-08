let socket = io();
socket.on('connect', function () {
    socket.emit('index_connected_timeline');
    socket.emit('index_connected');
});

socket.on('peopleList', function (data) {
    let items = document.getElementsByClassName('placeholder-glow');
    Array.from(items).forEach(function (item) {
        item.remove();
    });

    let list = document.getElementById('PeopleList');
    let textSecondary = ""
    if (data.person.is_paused) {
        textSecondary += "\"text-secondary\""
    }
    let badge = ""
    if (data.answered_count !== 0) {
        if ((data.correct_count / data.answered_count) > 0.75) {
            badge += "<span class=\"badge bg-success rounded-pill\">" + Math.round((data.correct_count / data.answered_count) * 1000) / 10 + "%</span>"
        } else if ((data.correct_count / data.answered_count) > 0.5) {
            badge += "<span class=\"badge bg-primary rounded-pill\">" + Math.round((data.correct_count / data.answered_count) * 1000) / 10 + "%</span>"
        } else if ((data.correct_count / data.answered_count) > 0) {
            badge += "<span class=\"badge bg-warning rounded-pill\">" + Math.round((data.correct_count / data.answered_count) * 1000) / 10 + "%</span>"
        }
    } else {
        badge += "<span class=\"badge bg-danger rounded-pill\">0 %</span>"
    }
    list.innerHTML += "<a href=\"/statistic/" + data.person.id + "\"" + "class=\"list-group-item d-flex justify-content-between align-items-center " +
        textSecondary + "\">" + data.person.full_name + badge + "</a>";
})

socket.on('timeline', function (json_data) {
    let data = JSON.parse(json_data);
    bubble_chart.data.datasets[0].data = data.timeline_data_correct;
    bubble_chart.data.datasets[1].data = data.timeline_data_incorrect;
    bubble_chart.update();
})
const bubble_chart_canvas = document.getElementById('TimeLine');

const bubble_chart = new Chart(
    bubble_chart_canvas,
    {
        type: 'bubble',
        data: {
            datasets: [
                {
                    label: 'Questions answered correctly',
                    data: [],
                    backgroundColor: "rgba(123,185,72,0.2)",
                    borderColor: "rgb(122,204,81)",
                    hoverBackgroundColor: "rgba(138,196,76,0.4)",
                    hoverBorderColor: "rgb(136,187,73)",
                },
                {
                    label: 'Questions answered incorrectly',
                    data: [],
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
            scales: {
                y: {
                    grid: {
                        display: true,
                        color: "rgba(104,157,61,0.2)"
                    },
                    display: false,
                    reverse: true,
                    grace: '10%'
                },
                x: {
                    type: 'time',
                    ticks: {
                        major: {
                            enabled: true
                        },
                        autoSkip: true,
                        autoSkipPadding: 50,
                        maxRotation: 0,
                    },
                    grid: {
                        display: true
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let date = new Date(context.parsed.x).toString().split(' ')
                            let label = date[1] + ' ' + date[2] + ': '
                            if (context.parsed.y !== null) {
                                label += id_to_name[context.parsed.y];
                            }
                            return label;
                        }
                    }
                },
                zoom: {
                    pan: {
                        enabled: true,
                        mode: 'xy',
                        modifierKey: 'ctrl',
                    },
                    zoom: {
                        mode: 'xy',
                        drag: {
                            enabled: true,
                            borderColor: 'rgb(54, 162, 235)',
                            borderWidth: 1,
                            backgroundColor: 'rgba(54, 162, 235, 0.3)'
                        }
                    }
                }
            }
        }
    }
)


bubble_chart_canvas.ondblclick = (evt) => {
    bubble_chart.resetZoom();
};

bubble_chart_canvas.onclick = (evt) => {
    const res = bubble_chart.getElementsAtEventForMode(evt, 'nearest', {intersect: true}, true);

    if (res.length === 0) {
        return;
    }

    window.location.href = "/statistic/" + bubble_chart.data.datasets[res[0].datasetIndex].data[res[0].index].y;
};

