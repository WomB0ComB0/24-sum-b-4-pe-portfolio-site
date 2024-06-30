function postToMailto() {
  const field1 = document.querySelector("#name").value;
  const field2 = document.querySelector("#profession").value;
  const field3 = document.querySelector("#company").value;
  const field4 = document.querySelector("#email").value;
  const field5 = document.querySelector("#subject").value;
  const field6 = document.querySelector("#message").value;

  const subject = `${field2} - ${field3} - ${field5}`;
  const body = `${field6}\n\n-${field1}\n${field4}`;

  let mailtoLink = `mailto:mikeodnis3242004@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

  setTimeout(() => {
    window.open(mailtoLink, '_blank');
  }, 1000);

  return false;
}
