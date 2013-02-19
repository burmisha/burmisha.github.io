findSet = function(hid) {
	for (var j = 0; j < allPhotos.length; j++) {
		if (hid.localeCompare(allPhotos[j].id) == 0){
			return j;
		}
	};
	alert("none for " + hid);
};

addPhotoset = function(photoset) {
	var id = "div#" + photoset.id;
	$(id).append('<h2>' + photoset.title + '</h2>');
	var filenames = "", cl = "";
	if (photoset.size == 1) {
		filenames = photoset.filenames;
		cl = "bigphoto";
	} else {
		filenames = photoset.filenames_small;
		cl = "smallphoto";
	};
	for (var i = 0; i < filenames.length; i++) {
		var newdiv = '<div style="background-image:url('+ filenames[i] + ')"></div>';
		$(id).append(newdiv);
	};
	$(id + " div").addClass(cl);
	$(id).append('<p>' + photoset.text + '</p>');
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
			var photoset = allPhotos[j];
			$("#content").append('<div class="photoset" id="'+ photoset.id + '"></div>');
			addPhotoset(photoset);
			$('#content').on('click', "div.photoset", function(event){
				var photoset = allPhotos[findSet($(this).attr("id"))];
				$("#" + photoset.id).empty();
				photoset.size = 1 - photoset.size;
				addPhotoset(photoset); 
				event.stopImmediatePropagation()
			});
		};
	});
})
