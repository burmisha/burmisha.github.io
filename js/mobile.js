findSet = function(hid) {
	for (var j = 0; j < allPhotos.length; j++) {
		if (hid.localeCompare(allPhotos[j].id) == 0){
			return j;
		}
	};
	alert("none for " + hid);
};

addPhotoset = function(h, cl, prefix) {
	hid = "#" + h.id;
	$(hid).append('<h2>' + h.title + '</ph2>');
	for (var i = 0; i < h.middles.length; i++) {
		$(hid).append('<div style="background-image:url('+ prefix + h.prefix + h.middles[i] + h.suffix + ')"></div>');
	};
	$(hid + " div").addClass(cl);
	$(hid).append('<p>' + h.text + '</p>');
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
