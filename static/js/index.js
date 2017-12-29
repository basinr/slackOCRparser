$(function() {
    console.log( "ready!" );
    document.getElementById('email_submit').addEventListener('click', function(e) {
      name = $("#exampleModal2 #sender-name").val().trim();
      sender_email = $("#exampleModal2 #sender-email").val().trim();
      message = $("#exampleModal2 #sender-msg").val().trim();
      console.log(message);
      $.ajax({
            type : "POST",
            url : "/contact_form",
            data: JSON.stringify({name: name, email: sender_email, message: message}),
            contentType: 'application/json;charset=UTF-8',
        });
      e.preventDefault();
    });
});