let socket = io();

window.onload = function () {
    new bootstrap.Modal("#question_modal");
    document.querySelectorAll(".question_stat").forEach(function (question_stat) {
        question_stat.addEventListener("click", function (event) {
            document.querySelector("#question_modal").querySelectorAll(".datable").forEach(function (datable) {
                datable.innerHTML = "";
                datable.classList.add("placeholder", "col-5");
            });
            bootstrap.Modal.getInstance("#question_modal").show();

            document.querySelector("#planquestionform-question_id").value = event.currentTarget.dataset.question;

            socket.emit("get_question_stat", {
                person_id: parseInt(document.querySelector("#person").dataset.person),
                question_id: parseInt(event.currentTarget.dataset.question)
            });
        });
    });
};

socket.on("question_info", function (data) {
    let modal = document.querySelector("#question_modal");

    modal.querySelector(".q_text").innerHTML = data.question.text;
    modal.querySelector(".q_groups").innerHTML = data.question.groups.map((g) => g.name).join(", ");
    modal.querySelector(".q_level").innerHTML = data.question.level;
    modal.querySelector(".q_correct").innerHTML = data.question.options[data.question.answer - 1];

    let answers_tbl = modal.querySelector(".q_answers");
    answers_tbl.innerHTML = "";
    data.answers.forEach(function (answer) {
        let tr_style = "";
        switch (answer.state) {
            case "CORRECT":
                tr_style = "table-success";
                break;
            case "INCORRECT":
                tr_style = "table-warning";
                break;
            case "IGNORED":
                tr_style = "table-info";
                break;
            case "NOT_ANSWERED":
                tr_style = "table-secondary";
                break;
        }
        answers_tbl.innerHTML += `<tr class="${tr_style}"><td>${data.question.options[answer.person_answer - 1]}</td>
<td>${answer.ask_time}</td>
<td>${answer.answer_time}</td></tr>`;
    });

    modal.querySelectorAll(".datable").forEach(function (datable) {
        datable.classList.remove("placeholder", "col-5");
    });

})