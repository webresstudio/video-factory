// Recorta a la persona de cada cuadro con Vision (macOS) y guarda máscaras PNG.
// Uso: segment_person <carpeta_cuadros_png> <carpeta_mascaras>
// Calidad: .accurate (lenta pero con buen pelo y bordes).
import Foundation
import Vision
import CoreImage
import AppKit

let args = CommandLine.arguments
guard args.count >= 3 else { print("uso: segment_person in_dir out_dir"); exit(1) }
let inDir = URL(fileURLWithPath: args[1]), outDir = URL(fileURLWithPath: args[2])
try? FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)
let files = try FileManager.default.contentsOfDirectory(atPath: inDir.path).filter { $0.hasSuffix(".png") }.sorted()
let ctx = CIContext()
let req = VNGeneratePersonSegmentationRequest()
req.qualityLevel = .accurate
req.outputPixelFormat = kCVPixelFormatType_OneComponent8
var n = 0
for f in files {
    let url = inDir.appendingPathComponent(f)
    guard let img = CIImage(contentsOf: url) else { continue }
    let h = VNImageRequestHandler(ciImage: img, options: [:])
    try h.perform([req])
    guard let mask = req.results?.first?.pixelBuffer else { continue }
    var m = CIImage(cvPixelBuffer: mask)
    let sx = img.extent.width / m.extent.width, sy = img.extent.height / m.extent.height
    m = m.transformed(by: CGAffineTransform(scaleX: sx, y: sy))
    guard let cg = ctx.createCGImage(m, from: img.extent) else { continue }
    let rep = NSBitmapImageRep(cgImage: cg)
    try rep.representation(using: .png, properties: [:])!.write(to: outDir.appendingPathComponent(f))
    n += 1
}
print("máscaras: \(n)")
