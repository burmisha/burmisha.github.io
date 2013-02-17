$(function(){
	$("#links").click(function(){
		$("#content").load("links.html");
	});

	$("#bio").click(function(){
		$("#content").load("bio.html");
	});

	$("#photo").click(function(){
		$("#content").load("photo.html", function(){
			for (var j = 0; j < allPhotos.length; j++) {
				h = allPhotos[j];
				for (var i = 0; i < h.middles.length; i++) {
					var url = h.path_small + h.prefix + h.middles[i]+h.suffix;
					$(h.id).append('<div class="smallphoto" style="background-image:url('+ url + ')"></div>');
				};
			};
		});

		for (var j = 0; j < allPhotos.length; j++) {
			var h = allPhotos[j];
			$('#content').on('click', h.id+" .smallphoto", function(){
				$(h.id).empty();
				// alert(h.id);
				for (var i = 0; i < h.middles.length; i++) {
					var url = h.path + h.prefix + h.middles[i]+h.suffix;
					$(h.id).append('<div class="bigphoto" style="background-image:url('+ url + ')"></div>');
				};
				return false;
			});

			$('#content').on('click', h.id + " .bigphoto", function(){
				$(h.id).empty();
				for (var i = 0; i < h.middles.length; i++) {
					var url = h.path_small + h.prefix + h.middles[i]+h.suffix;
					$(h.id).append('<div class="smallphoto" style="background-image:url('+ url + ')"></div>');
				};
				return false;
			});
		};
	});
})
