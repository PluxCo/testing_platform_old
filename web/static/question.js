const table = new DataTable('#table', {
    ajax: '/questions_ajax',
    processing: true,
    serverSide: true,
    columns: [{}, {}, {}, {width: "30%"}, {}, {orderable: false}, {}, {}]
});

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
    socket.emit("get_question_stat", {question_id: table.data()[selected_id][0]});
});

document.querySelector("#delete_button").addEventListener("click", function () {
    let selected_id = table.rows(".selected")[0][0];
    console.log(selected_id);
    socket.emit("get_question_stat", {question_id: table.data()[selected_id][0]});
});

socket.on("question_info", function (data) {
    
    console.log(data);
    document.getElementById('question-id').value = data.question.id;
    document.getElementById('question-text').value = data.question.text;
    document.getElementById('question-subject').value = data.question.subject;
    document.getElementById('question-options').value = data.question.options.join("\n");
    document.getElementById('question-answer').value = data.question.answer;
    document.getElementById('question-level').value = data.question.level;
    document.getElementById('question-article').value = data.question.article_url;
    console.log(data.question.groups.map((group) => group.id));
    $("#question-groups").selectpicker("val", data.question.groups.map((group) => String(group.id)));

    document.getElementById('question-id-delete').value = data.question.id;


});


document.querySelector('#delete-btn').addEventListener('click', function () {
    table.row('.selected').remove().draw(false);
    const id = table.rows('.selected').nodes()[0].cells[0].innerText;

    document.getElementById('edit_button').setAttribute('disabled', '');
    document.getElementById('delete_button').setAttribute('disabled', '');
});

document.addEventListener("DOMContentLoaded", function () {
    var is_openCheckbox = document.getElementById("createquestionform-is_open");
    var optionsField = document.getElementById("createquestionform-options");
    var answerField = document.getElementById("createquestionform-answer");
    var optionsLabel = document.getElementById("createquestionform-options-label")
    var answerLabel = document.getElementById("createquestionform-answer-label")
    is_openCheckbox.addEventListener("change", function () {
        if (is_openCheckbox.checked) {
            optionsField.style.display = "none";
            optionsLabel.style.display = "none";
            answerLabel.textContent = "Answer";
            answerField.style.height = "12rem";
            optionsField.value = "";
            answerField.placeholder = "На мой взгляд, это mkdir."

        } else {
            optionsField.style.display = "block";
            optionsLabel.style.display = "block";
            answerLabel.textContent = "Answer index";
            answerField.style.height = "1rem";
            answerField.placeholder = "1"

        }
    });
});