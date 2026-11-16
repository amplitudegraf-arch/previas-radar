// Recorta um quadrado centrado no maior rosto da foto (Vision, macOS).
// Uso: swift recortar_rosto.swift entrada.jpg saida.jpg 320
import Foundation
import Vision
import CoreImage
import ImageIO
import UniformTypeIdentifiers

let a = CommandLine.arguments
let lado = CGFloat(Double(a[3]) ?? 320)
guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: a[1]) as CFURL, nil),
      let img0 = CGImageSourceCreateImageAtIndex(src, 0, nil) else { print("erro: leitura"); exit(1) }
// respeita a orientação EXIF
let props = CGImageSourceCopyPropertiesAtIndex(src, 0, nil) as? [CFString: Any]
let ori = (props?[kCGImagePropertyOrientation] as? UInt32) ?? 1
let ci = CIImage(cgImage: img0).oriented(CGImagePropertyOrientation(rawValue: ori) ?? .up)
let ctx = CIContext()
guard let img = ctx.createCGImage(ci, from: ci.extent) else { exit(1) }
let W = CGFloat(img.width), H = CGFloat(img.height)

let req = VNDetectFaceRectanglesRequest()
try? VNImageRequestHandler(cgImage: img).perform([req])
let rostos = (req.results ?? []).sorted { $0.boundingBox.width * $0.boundingBox.height > $1.boundingBox.width * $1.boundingBox.height }

var cx = W / 2, cy = H * 0.35, q = min(W, H), fw0: CGFloat = 0, fh0: CGFloat = 0, topo: CGFloat = 0
if let f = rostos.first?.boundingBox {
    // Vision usa origem embaixo à esquerda, valores de 0 a 1
    let fw = f.width * W, fh = f.height * H
    fw0 = fw; fh0 = fh
    topo = (1 - f.maxY) * H                    // alto do rosto (testa), de cima para baixo
    cx = (f.midX) * W
    cy = (1 - f.midY) * H + fh * 0.25          // desce um pouco: inclui queixo e ombros
    q = min(max(fw, fh) * 2.6, min(W, H))
    print("rosto", rostos.count)
} else {
    print("sem rosto: recorte no alto, centro")
}
var x = cx - q / 2, y = cy - q / 2
if rostos.first != nil {
    // Retrato fechado: o quadrado pode passar da borda da foto. Nesse caso
    // completamos com a cor do fundo, para a cabeça não ficar cortada.
    q = min(max(fw0 * 2.6, fh0 * 2.6), W)   // nunca mais largo que a foto: sem sobra nas laterais
    x = cx - q / 2; y = cy - q / 2
    x = q <= W ? max(0, min(x, W - q)) : (W - q) / 2
    if q <= H { y = min(y, H - q) } else { y = H - q }   // embaixo nunca sobra vazio
    y = min(y, topo - fh0 * 0.6)                // sempre um espaço acima do cabelo
} else {
    x = max(0, min(x, W - q)); y = max(0, min(y, H - q))
}

// cor de fundo: média da faixa de cima da foto
func corMedia(_ r: CGRect) -> CGColor {
    let px = CGContext(data: nil, width: 1, height: 1, bitsPerComponent: 8, bytesPerRow: 4,
                       space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    px.interpolationQuality = .medium
    if let pedaco = img.cropping(to: r) { px.draw(pedaco, in: CGRect(x: 0, y: 0, width: 1, height: 1)) }
    let d = px.data!.assumingMemoryBound(to: UInt8.self)
    return CGColor(red: CGFloat(d[0]) / 255, green: CGFloat(d[1]) / 255, blue: CGFloat(d[2]) / 255, alpha: 1)
}
let fundo = corMedia(CGRect(x: 0, y: 0, width: W, height: max(2, H * 0.04)))

let s = lado / q
let cs = CGColorSpaceCreateDeviceRGB()
let c = CGContext(data: nil, width: Int(lado), height: Int(lado), bitsPerComponent: 8, bytesPerRow: 0, space: cs,
                  bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
c.interpolationQuality = .high
c.setFillColor(fundo)
c.fill(CGRect(x: 0, y: 0, width: lado, height: lado))
c.draw(img, in: CGRect(x: -x * s, y: lado + y * s - H * s, width: W * s, height: H * s))
let dest = CGImageDestinationCreateWithURL(URL(fileURLWithPath: a[2]) as CFURL, UTType.jpeg.identifier as CFString, 1, nil)!
CGImageDestinationAddImage(dest, c.makeImage()!, [kCGImageDestinationLossyCompressionQuality: 0.82] as CFDictionary)
CGImageDestinationFinalize(dest)
