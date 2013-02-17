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
	$("#photo").click(function(event){
		$("#content").load("photo.html", 
							function(){
			Diana_20130212 = ['1302-burmisha-0056', '1302-burmisha-0057', '1302-burmisha-0059'];
			for (var i = 0; i < Diana_20130212.length; i++) {
				var url = 'photo/20130212_Diana_small/'+Diana_20130212[i]+'.jpg';
				$("#Diana_20130212").append('<div style="background:url('+ url + ')"></div>');
			};
		});
	});
})
