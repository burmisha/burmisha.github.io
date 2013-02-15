/*
$(function(){
	$("span.button#set-mobile").click(function(event){
		$("*").toggleClass('mobile');
	});
})
*/

$(function(){
	$("#links").click(function(event){
		$("#content").load("links.html");
	});
	$("#bio").click(function(event){
		$("#content").load("bio.html");
	});
})
