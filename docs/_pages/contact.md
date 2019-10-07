---
permalink: /contact/
---

<div class="contact-page">
  <div id="pop-up"></div>
  <div class="contact-form">
      <form id="contact-form" action="" onsubmit="return ValidateForm(event)">
        <span class="contact-form-title">Contact Us</span>
        <div class="wrap-input">
          <span class="label-input">Full Name</span>
          <input class="input" type="text" name="Name" placeholder="Enter Your Name" />
          <span class="input-underline"></span>
        </div>
        <div class="wrap-input">
          <span class="label-input">Email</span>
          <input class="input" type="text" name="Email" placeholder="Enter Your Email" />
        </div>      
        <div class="wrap-input">
          <span class="label-input">Message</span>
          <textarea name="Message" class="message" placeholder='Put Your Message Here...' rows='8' cols='50'></textarea>
        </div>
        <div class="g-recaptcha" data-sitekey="6LfK77oUAAAAAHCy4-dYlv9sp4-SAJSQxBIVf4nY"></div>
        <input type='submit' class="form-button" value='Send message' />
      </form>
  </div>
</div>

<script type='text/javascript'>

    function ValidateForm(event) {

      event.preventDefault();

      if (ValidateCaptcha()) {
        submitForm();

        setTimeout(function(){
          showPopUp("success", "Your form has been submitted!");
          grecaptcha.reset();
          document.getElementById("contact-form").reset();
        }, 1000);

      } else {
        showPopUp("error", "The form could not be submitted. Please fill in all the required fields.");
      }
      return false;
    }

    function ValidateCaptcha() {      
      var response = grecaptcha.getResponse();
      return (response.length != 0);
    }

    function showPopUp (type, message){
      var popUp = document.getElementById("pop-up");
      var icon = "";

      if (type == "success") {
        popUp.classList.add("success");
        popUp.classList.remove("error");
        icon = '<i class="fa fa-check"></i>';
      } else {
        popUp.classList.add("error");
        popUp.classList.remove("success");
        icon = '<i class="fa fa-times-circle"></i>';
      }

      popUp.classList.add("visible");
      popUp.innerHTML = icon + message;

      setTimeout(function() {
         popUp.classList.remove("visible");
       }, 4000);
     }

    function submitForm(){
      var formData = new FormData();

      var inputs = document.getElementsByClassName("input");
      for (var i=0; i < inputs.length; i++) {
          formData.append(inputs[i].name, inputs[i].value);
      }

      var message = document.getElementsByClassName("message")[0];
      formData.append(message.name, message.value);


      var xmlHttp = new XMLHttpRequest();
      xmlHttp.open("post", "https://getsimpleform.com/messages?form_api_token=c3b9960a747219449196dcca00487a9c");
      xmlHttp.send(formData);
    }

</script>
