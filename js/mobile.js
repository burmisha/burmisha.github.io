$(function(){
	$("#links").click(function(){
		$("#content").load("links.html");
	});

	$("#bio").click(function(){
		$("#content").load("bio.html");
	});

	$("#photo").click(function(){
		$("#content").load("photo.html", function(){
			var h = Diana_21;
			for (var i = 0; i < h.middles.length; i++) {
				var url = h.path_small + h.prefix + h.middles[i]+h.suffix;
				$(h.id).append('<div class="smallphoto" style="background-image:url('+ url + ')"></div>');
			};
		});
	});

	var h = Diana_21;
	$('#content').on('click', ".smallphoto", function(){
		$(h.id).empty();
		for (var i = 0; i < h.middles.length; i++) {
			var url = h.path + h.prefix + h.middles[i]+h.suffix;
			$(h.id).append('<div class="bigphoto" style="background-image:url('+ url + ')"></div>');
		};
		return false;
	});

	$('#content').on('click', ".bigphoto", function(){
		$(h.id).empty();
		for (var i = 0; i < h.middles.length; i++) {
			var url = h.path_small + h.prefix + h.middles[i]+h.suffix;
			$(h.id).append('<div class="smallphoto" style="background-image:url('+ url + ')"></div>');
		};
		return false;
	});
})
