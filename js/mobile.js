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
			//alert(h.id);
			$("#content").append('<div class="photoset" id='+ h.id + '></div>');
			for (var i = 0; i < h.middles.length; i++) {
				var url = h.path_small + h.prefix + h.middles[i] + h.suffix;
				$(hid).append('<div class="smallphoto" style="background-image:url('+ url + ')"></div>');
			};

			//$('#content').on('click', "{id: $(this).attr("id")}", function(event){
			$('#content').on('click', "div.photoset", function(event){
				var p = findSet($(this).attr("id"));
				var h = allPhotos[p];
				var hid = "#" + h.id;
				small = $(hid+" div").hasClass("smallphoto");
				$(hid).empty();
				alert(small)
				if (small) {
					for (var i = 0; i < h.middles.length; i++) {
						var url = h.path + h.prefix + h.middles[i] + h.suffix;
						$(hid).append('<div style="background-image:url('+ url + ')"></div>');
					};
					$(hid+" div").addClass("bigphoto");
					alert('ok');
				} else {
					for (var i = 0; i < h.middles.length; i++) {
						var url = h.path_small + h.prefix + h.middles[i] + h.suffix;
						$(hid).append('<div style="background-image:url('+ url + ')"></div>');
					};
					$(hid+" div").addClass("smallphoto");
					alert('ok');
				}
				event.stopPropagation();
				return false;
			});

			/*$(hid).on('click', ".bigphoto", function(){
				$(hid).empty();
				//alert('cleared ' + hid);
				for (var i = 0; i < h.middles.length; i++) {
					var url = h.path_small + h.prefix + h.middles[i] + h.suffix;
					$(hid).append('<div class="smallphoto" style="background-image:url('+ url + ')"></div>');
				};
				return false;
			});*/
			hid = "qqu";
		};
	});
})
