import Foundation
import AppKit
import CoreText
import CoreGraphics
import ImageIO

let base = URL(fileURLWithPath: FileManager.default.currentDirectoryPath).appendingPathComponent("docs/assets")
let name = CommandLine.arguments[1]
let data = try! Data(contentsOf: URL(fileURLWithPath: "docs/briefs/" + name + ".json"))
let copy = try! JSONSerialization.jsonObject(with: data) as! [String: Any]
func value(_ key: String) -> String { copy[key] as! String }
let destination = base.appendingPathComponent(name + ".pdf")

var media = CGRect(x: 0, y: 0, width: 595.28, height: 841.89)
let meta = [kCGPDFContextTitle as String: "a365-toolkit", kCGPDFContextAuthor as String: "", kCGPDFContextSubject as String: "Executive capability brief"] as CFDictionary
guard let context = CGContext(destination as CFURL, mediaBox: &media, meta) else { fatalError("PDF context unavailable") }
context.beginPDFPage(nil)
let navy = NSColor(calibratedRed: 0.10, green: 0.17, blue: 0.24, alpha: 1)
let ink = NSColor(calibratedRed: 0.20, green: 0.23, blue: 0.26, alpha: 1)
let muted = NSColor(calibratedRed: 0.39, green: 0.43, blue: 0.46, alpha: 1)
let accent = NSColor(calibratedRed: 0.19, green: 0.39, blue: 0.43, alpha: 1)
let border = NSColor(calibratedWhite: 0.82, alpha: 1)
func line(_ y: CGFloat, _ color: NSColor = border, _ width: CGFloat = 0.5, _ x: CGFloat = 42, _ end: CGFloat = 553) {
    context.setStrokeColor(color.cgColor); context.setLineWidth(width)
    context.move(to: CGPoint(x: x, y: media.height-y)); context.addLine(to: CGPoint(x: end, y: media.height-y)); context.strokePath()
}
func text(_ string: String, _ x: CGFloat, _ y: CGFloat, _ width: CGFloat, _ height: CGFloat, _ size: CGFloat = 10, _ font: String = "Helvetica", _ color: NSColor = ink, _ leading: CGFloat = 3) {
    let paragraph = NSMutableParagraphStyle(); paragraph.lineSpacing = leading
    let attrs: [NSAttributedString.Key: Any] = [.font: NSFont(name: font, size: size)!, .foregroundColor: color, .paragraphStyle: paragraph]
    let content = NSAttributedString(string: string, attributes: attrs)
    let framesetter = CTFramesetterCreateWithAttributedString(content)
    let path = CGPath(rect: CGRect(x:x,y:media.height-y-height,width:width,height:height),transform:nil)
    let frame = CTFramesetterCreateFrame(framesetter, CFRange(location:0,length:content.length),path,nil)
    let visible = CTFrameGetVisibleStringRange(frame)
    if visible.length < content.length { fatalError("Text overflow: \(string)") }
    CTFrameDraw(frame, context)
}
text("A365-TOOLKIT  /  SECURITY ADMINISTRATION",42,35,390,15,8.5,"Helvetica-Bold",accent)
text(value("kind"),425,35,130,15,7.5,"Helvetica",muted)
line(59,navy,1)
text(value("title"),42,82,510,52,35,"Georgia",navy,1)
text(value("subtitle"),42,143,510,42,12,"Helvetica",muted,3)
line(201)
text("PURPOSE",42,221,95,17,8.5,"Helvetica-Bold",accent)
text(value("purpose"),151,219,396,67,11,"Helvetica",ink,3)
text(value("tableTitle"),42,305,450,16,8.5,"Helvetica-Bold",accent)
text("SERVICE",42,334,95,15,8,"Helvetica-Bold",muted)
text("CAPABILITY",142,334,300,15,8,"Helvetica-Bold",muted)
text("DELIVERY",447,334,110,15,8,"Helvetica-Bold",muted)
line(354,navy,0.7)
let rows = copy["rows"] as! [[String]]
for (i,row) in rows.enumerated() {
 let y = CGFloat(368 + i*49)
 text(row[0],42,y,95,35,10,"Helvetica-Bold",navy,2)
 text(row[1],142,y,300,37,9.8,"Helvetica",ink,2)
 text(row[2],447,y+1,107,36,8.5,"Helvetica",muted,2)
 line(y+36)
}
text(value("leftTitle"),42,589,245,17,8.5,"Helvetica-Bold",accent)
text(value("left"),42,612,245,105,10,"Helvetica",ink,4)
text(value("rightTitle"),311,589,245,17,8.5,"Helvetica-Bold",accent)
text(value("right"),311,612,245,105,10,"Helvetica",ink,4)
text(value("note"),42,737,511,49,9.2,"Helvetica",muted,3)
line(801)
text(value("footer"),42,812,500,17,7.2,"Helvetica",muted)
text("01",538,812,15,15,8,"Helvetica",muted)
context.endPDFPage(); context.closePDF()
// Render a local preview for layout inspection; the deliverable remains vector text.
let document = CGPDFDocument(destination as CFURL)!
let page = document.page(at:1)!
let factor: CGFloat = 2
let bitmap = CGContext(data:nil,width:Int(media.width*factor),height:Int(media.height*factor),bitsPerComponent:8,bytesPerRow:0,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
bitmap.setFillColor(NSColor.white.cgColor);bitmap.fill(CGRect(x:0,y:0,width:media.width*factor,height:media.height*factor))
bitmap.scaleBy(x:factor,y:factor);bitmap.drawPDFPage(page)
let preview = URL(fileURLWithPath:"/tmp/" + name + ".png")
let output = CGImageDestinationCreateWithURL(preview as CFURL,"public.png" as CFString,1,nil)!
CGImageDestinationAddImage(output,bitmap.makeImage()!,nil);CGImageDestinationFinalize(output)
print("PDF: \(destination.path)")
print("Pages: \(document.numberOfPages)")
print("Preview: \(preview.path)")
