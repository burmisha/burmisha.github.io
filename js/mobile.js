$(function(){
	var Diana_21 = {
				path: 'photo/20130212_Diana/',
				path_small: 'photo/20130212_Diana_small/',
				prefix: '1302-burmisha-',
				suffix: '.jpg',
				middles: ['0056','0057','0059','0062','0063','0064','0065','0068','0069','0071'],
				id: '#Diana_20130212',
	};
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
	$('#avatar').click(function(){
		$(h.id).empty();
			for (var i = 0; i < h.middles.length; i++) {
			var url = h.path + h.prefix + h.middles[i]+h.suffix;
			$(h.id).append('<div class="bigphoto" style="background-image:url('+ url + ')"></div>');
		};
	});	
})
