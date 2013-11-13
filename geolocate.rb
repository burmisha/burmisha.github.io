#!/Users/burmisha/.rvm/rubies/ruby-2.0.0-p247/bin/ruby
require 'exifr'
require 'net/http'
require 'stringio'

file_id = '9480/82500796.17/0_cbadd_d8dd2315'
Net::HTTP.start("img-fotki.yandex.ru") do |http|
    path = "/get/" + file_id + "_orig.jpg"
    resp = http.get(path)
    jpeg = StringIO.new
    jpeg << resp.body
    jpeg.rewind
    latitude = EXIFR::JPEG.new(jpeg).gps.latitude
    puts latitude
end

folder="/Users/burmisha/Dropbox/Photo/2013/2013.08 London/DB/"

File.open('coordinates.tmp', 'w') do |output|
  Dir.glob(folder + '*.jpg') do |file|
    coordinates = ""
    begin 
      latitude = EXIFR::JPEG.new(file).gps.latitude
      longitude = EXIFR::JPEG.new(file).gps.longitude
      output.puts "#{latitude.round(6)},#{longitude.round(6)}"
    rescue
      output.puts "\n"
    end
  end
end
