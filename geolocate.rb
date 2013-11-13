#!/Users/burmisha/.rvm/rubies/ruby-2.0.0-p247/bin/ruby
require 'exifr'
require 'net/http'
require 'yaml'
require 'json'

file = 'db/index.html'
thing = YAML.load_file(file)
gps = []

Net::HTTP.start("img-fotki.yandex.ru") do |http|
  thing['photos'].each_with_index { |image, index|
    path = "/get/" + image['url'] + "_orig.jpg"
    resp = http.get(path)
    jpeg = StringIO.new
    jpeg << resp.body
    begin
      jpeg.rewind
      latitude = EXIFR::JPEG.new(jpeg).gps.latitude.round(6)
      jpeg.rewind
      longitude = EXIFR::JPEG.new(jpeg).gps.longitude.round(6)
      puts path + ": " +"#{latitude},#{longitude}"
      gps << {'type' => 'Feature' ,
              'geometry' => {'type'=> 'Point', 'coordinates' => ["#{longitude}", "#{latitude}"]} ,
              'properties'=> { 'title' => "Marker #{index}",
                               'image_url' => image['url'],
                               'marker-color' => '#CC0033'} }
    rescue
      puts path + ": " + "\n"
    end
  }
end

File.open(file + '.json', 'w') {|f| f.write 'var geoJson = ' + gps.to_json + ';'}
