findSet = function(hid) {
	for (var j = 0; j < allPhotos.length; j++) {
		if (hid.localeCompare(allPhotos[j].id) == 0){
			return j;
		}
	};
	alert("none for " + hid);
};


$(function(){
	$("#links").click(function(){
		$("#content").load("links.html");
	});

	$("#bio").click(function(){
		$("#content").load("bio.html");
	});

	$("#photo").click(function(){
		$("#content").empty();
		for (var j = 0; j < allPhotos.length; j++) {
			var h = allPhotos[j];
			var hid = "#" + h.id;
			$("#content").append('<div class="photoset" id='+ h.id + '></div>');
			for (var i = 0; i < h.middles.length; i++) {
				var url = h.path_small + h.prefix + h.middles[i] + h.suffix;
				$(hid).append('<div class="smallphoto" style="background-image:url('+ url + ')"></div>');
			};

			$('#content').on('click', "div.photoset", function(event){
				var h = allPhotos[findSet($(this).attr("id"))];
				var hid = "#" + h.id;
				small = $(hid+" div").hasClass("smallphoto");
				$(hid).empty();
				var prefix;
				if (small) { prefix = h.path; } 
				else { prefix = h.path_small; };
				for (var i = 0; i < h.middles.length; i++) {
					$(hid).append('<div style="background-image:url('+ prefix + h.prefix + h.middles[i] + h.suffix + ')"></div>');
				};
				if (small) { $(hid+" div").addClass("bigphoto"); } 
				else { $(hid+" div").addClass("smallphoto"); };
				event.stopImmediatePropagation()
			});
		};
	});
})
