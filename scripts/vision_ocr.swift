import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count >= 2 else {
    fputs("usage: swift vision_ocr.swift <image-path>\n", stderr)
    exit(2)
}

let path = CommandLine.arguments[1]
let url = URL(fileURLWithPath: path)
guard let image = NSImage(contentsOf: url) else {
    fputs("cannot load image\n", stderr)
    exit(1)
}

guard let tiff = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiff),
      let cgImage = bitmap.cgImage else {
    fputs("cannot make cgimage\n", stderr)
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false
request.recognitionLanguages = ["zh-Hans", "en-US"]

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try handler.perform([request])

let width = CGFloat(cgImage.width)
let height = CGFloat(cgImage.height)

for observation in request.results ?? [] {
    guard let top = observation.topCandidates(1).first else { continue }
    let b = observation.boundingBox
    let x = b.minX * width
    let y = (1 - b.maxY) * height
    let w = b.width * width
    let h = b.height * height
    print("\(top.string)\t\(Int(x))\t\(Int(y))\t\(Int(w))\t\(Int(h))")
}
