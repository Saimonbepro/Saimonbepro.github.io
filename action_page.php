<?php

if(isset($_POST['send'])) {
   // Prepare the email
$to = 'james1234540491@gmail.com';

$name = $_POST['name'];
$mail_from = $_POST['email'];
   $subject = 'Message sent from website';
   $message = $_POST['message'];

$header = "From: $name <$mail_from>";

   // Send it
   $sent = mail($to, $subject, $message, $header);
   if($sent) {
   echo 'Your message has been sent successfully!';
   } else {
   echo 'Sorry, your message could not send.';
   }
}
?>