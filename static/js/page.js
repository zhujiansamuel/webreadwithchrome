var messagetext = JSON.stringify({"username":Username,"AuthenticationKey":UserAuthenticationKey})

$(document).ready(function() {
    window.postMessage({ type: "FROM_PAGE", text: messagetext  }, "*");
});