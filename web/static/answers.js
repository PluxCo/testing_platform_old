const table = new DataTable('#table', {
    ajax: {
        url: '/answers_ajax',
        data: function (d) {
            d.onlyOpen = document.getElementById("openCheck").checked;
            d.onlyUnverified = document.getElementById("unverifiedCheck").checked;
        }
    },
    processing: true,
    serverSide: true,
    searching: false,
    columns: [{}, {
        render: DataTable.render.datetime('dd.MM.yyyy HH:mm')
    }, {orderable: false}, {orderable: false}, {},
        {
            render: function (data) {
                return `<input type="number" min="0" max="1" step="0.01" onchange="markAsChanged(this)"
                        class="form-control accept-points" value="${data}" data-value="${data}" />`;
            }
        },
        {
            orderable: false,
            width: "8%",
            render: function (data, d, row) {
                return `<div class="col"><button class="btn btn-outline-danger btn-sm"
                        onclick="removeAnswer(this);" data-answer-id="${row[0]}">
                    <i class="bi bi-trash" style="font-size: 1rem; color: currentColor;"></i>
                </button>
                <button class="btn btn-outline-success btn-sm"
                        onclick="saveAnswer(this);" data-answer-id="${row[0]}">
                    <i class="bi bi-pencil-square" style="font-size: 1rem; color: currentColor;"></i>
                </button></div>`;
            }
        }
    ],
    order: [[1, 'desc']],
});

window.onload = function () {
    for (let el of document.querySelectorAll(".update-table")) {
        el.onchange = () => table.ajax.reload();
    }
}

socket = io();

socket.on("saved_success", () => {
    let toast = new bootstrap.Toast(".toast", {delay: 3000});
    toast.show();

});

function removeAnswer(sender) {
    document.getElementById('answer-id-delete').value = sender.dataset.answerId;
    new bootstrap.Modal('#deleteModal', {}).show();
}

function saveAnswer(sender) {
    const points = sender.closest("tr").querySelector(".accept-points");
    if (!points.checkValidity()) {
        points.reportValidity();
        return;
    }

    socket.emit("set_points", {answer_id: sender.dataset.answerId, points: points.value});

    points.dataset.value = points.value;
    markAsChanged(points);
}

function markAsChanged(sender) {
    if (sender.value != sender.dataset.value) {
        sender.style.borderColor = 'var(--bs-warning-border-subtle)';
    } else {
        sender.style.borderColor = '';
    }
}