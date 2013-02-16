/*
$(function(){
	$("span.button#set-mobile").click(function(event){
		$("*").toggleClass('mobile');
	});
})
*/

$(function(){
	prefix="http://examplebucket.s3-website-us-east-1.amazonaws.com/"
	$("#links").click(function(event){
		$("#content").load("links.html");
	});
	$("#bio").click(function(event){
		$("#content").load("bio.html");
	});
	$("#photo").click(function(event){
		$("#content").load("photo.html");
		//$("#20130212_Diana div")
	});
})
