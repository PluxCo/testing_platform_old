const table = new DataTable('#table', {
    ajax: '/questions_ajax',
    processing: true,
    serverSide: true,
    columns: [{}, {}, {}, {width: "30%"}, {}, {orderable: false}, {}, {},
        {
            orderable: false,
            width: "8%",
            render: function (data, d, row) {
                return `<div class="col"><button class="btn btn-outline-danger btn-sm"
                        onclick="removeQuestion(this);" data-question-id="${row[0]}">
                    <i class="bi bi-trash" style="font-size: 1rem; color: currentColor;"></i>
                </button>
                <button class="btn btn-outline-success btn-sm"
                        onclick="editQuestion(this);" data-question-id="${row[0]}">
                    <i class="bi bi-pencil-square" style="font-size: 1rem; color: currentColor;"></i>
                </button></div>`;
            }
        }
    ]
});

socket = io();

function removeQuestion(sender) {
    document.getElementById('question-id-delete').value = sender.dataset.questionId;
    new bootstrap.Modal('#deleteModal', {}).show();
}

function editQuestion(sender) {
    socket.emit("get_question_stat", {question_id: sender.dataset.questionId});
    new bootstrap.Modal('#editModal', {}).show();
}

socket.on("question_info", function (data) {

    console.log(data);
    document.getElementById('question-id').value = data.question.id;
    document.getElementById('question-text').value = data.question.text;
    document.getElementById('question-subject').value = data.question.subject;
    document.getElementById('question-options').value = data.question.options.join("\n");
    document.getElementById('question-answer').value = data.question.answer;
    document.getElementById('question-level').value = data.question.level;
    document.getElementById('question-article').value = data.question.article;
    console.log(data.question.groups.map((group) => group.id));
    $("#question-groups").selectpicker("val", data.question.groups.map((group) => String(group.id)));
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