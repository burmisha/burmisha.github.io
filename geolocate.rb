#!/Users/burmisha/.rvm/rubies/ruby-2.0.0-p247/bin/ruby
require 'exifr'
require 'net/http'
require 'yaml'
require 'json'

file = 'db/index.html'
gps = {'type' => 'FeatureCollection', 'features' => []}

Net::HTTP.start("img-fotki.yandex.ru") do |http|
  YAML.load_file(file)['photos'].each_with_index { |image, index|
    path = "/get/" + image['url'] + "_orig.jpg"
    jpeg = StringIO.new
    jpeg << http.get(path).body
    begin
      jpeg.rewind
      latitude = EXIFR::JPEG.new(jpeg).gps.latitude.round(6)
      jpeg.rewind
      longitude = EXIFR::JPEG.new(jpeg).gps.longitude.round(6)
      puts path + ": " +"#{latitude},#{longitude}"
      gps['features'] << {'type' => 'Feature' ,
              'geometry' => {'type'=> 'Point', 'coordinates' => ["#{longitude}", "#{latitude}"]} ,
              'properties'=> { 'image_url' => image['url']} }
    rescue
      puts path + ": " + "\n"
    end
  }
end

File.open(file + '.geojson', 'w') {|f| f.write JSON.pretty_generate gps}
