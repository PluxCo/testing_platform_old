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
    columns: [{}, {}, {orderable: false}, {orderable: false}, {width: "30%"}, {}
        // {
        //     render: function () {
        //         return `<button>edit</button>`;
        //     }
        // },
        // {
        //     render: function (data) {
        //         return `<button>remove</button>`;
        //     }
        // }
    ],
    order: [[1, 'desc']],
});

window.onload = function () {
    for (let el of document.querySelectorAll(".update-table")) {
        el.onchange = () => table.ajax.reload();
    }
}

socket = io();
table.on('click', 'tbody tr', (e) => {
    let classList = e.currentTarget.classList;

    if (classList.contains('selected')) {
        classList.remove('selected');
        document.getElementById('edit_button').disabled = true;
        document.getElementById('delete_button').disabled = true;
    } else {
        table.rows('.selected').nodes().each((row) => row.classList.remove('selected'));
        classList.add('selected');
        document.getElementById('edit_button').disabled = false;
        document.getElementById('delete_button').disabled = false;
    }

});


document.querySelector("#edit_button").addEventListener("click", function () {
    let selected_id = table.rows(".selected")[0][0];
    socket.emit("history_get_answer_info", {answer_id: table.data()[selected_id][0]});
});

document.querySelector("#delete_button").addEventListener("click", function () {
    let selected_id = table.rows(".selected")[0][0];
    socket.emit("history_get_answer_info", {answer_id: table.data()[selected_id][0]});
});

socket.on("answer_info", function (data) {
    document.getElementById('answer-id').value = data.answer.r_id;
    document.getElementById('answer-points').value = data.answer.points;
    document.getElementById('person_answer').innerHTML = data.answer.person_answer;
    document.getElementById('question_text').innerHTML = data.question.text;
    document.getElementById('question_options').innerHTML = '<ol>' + data.question.options.map(option => `<li>${option}</li>`).join('') + '</ol>';
    document.getElementById('correct_answer').innerHTML = data.question.answer;

    document.getElementById('answer-id-delete').value = data.answer.r_id;
});


document.querySelector('#delete-btn').addEventListener('click', function () {
    table.row('.selected').remove().draw(false);
    const id = table.rows('.selected').nodes()[0].cells[0].innerText;

    document.getElementById('edit_button').setAttribute('disabled', '');
    document.getElementById('delete_button').setAttribute('disabled', '');
});