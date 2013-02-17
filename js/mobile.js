findSet = function(hid) {
	for (var j = 0; j < allPhotos.length; j++) {
		if (hid.localeCompare(allPhotos[j].id) == 0){
			return j;
		}
	};
	alert("none for " + hid);
};


addPhotoset = function(h, cl, prefix) {
	for (var i = 0; i < h.middles.length; i++) {
		$("#" + h.id).append('<div style="background-image:url('+ prefix + h.prefix + h.middles[i] + h.suffix + ')"></div>');
	};
	$("#" + h.id + " div").addClass(cl);
}

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
			addPhotoset(h, "smallphoto", h.path_small);

			$('#content').on('click', "div.photoset", function(event){
				var h = allPhotos[findSet($(this).attr("id"))];
				var small = $("#" + h.id +" div").hasClass("smallphoto");
				$("#" + h.id).empty();
				if (small) { 
					addPhotoset(h, "bigphoto", h.path); 
				} 
				else { 
					addPhotoset(h, "smallphoto", h.path_small); 
				};
				event.stopImmediatePropagation()
			});
		};
	});
})
