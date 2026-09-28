// Shape each line of a text file with CoreText and print glyph ids + positions.
//   swiftc -O tools/coretext_shape.swift -o build/coretext_shape
//   build/coretext_shape FONT.ttf clusters.txt > out.txt
// Output per line: "gid:x:y" tokens in font units; a trailing "!" marks a fallback font.
import CoreText
import Foundation

let args = CommandLine.arguments
guard args.count == 3,
      let descs = CTFontManagerCreateFontDescriptorsFromURL(URL(fileURLWithPath: args[1]) as CFURL) as? [CTFontDescriptor],
      let desc = descs.first else {
    FileHandle.standardError.write("usage: coretext_shape FONT TEXTFILE\n".data(using: .utf8)!)
    exit(2)
}
let probe = CTFontCreateWithFontDescriptor(desc, 12, nil)
let upem = CGFloat(CTFontGetUnitsPerEm(probe))
let font = CTFontCreateWithFontDescriptor(desc, upem, nil)
let name = CTFontCopyPostScriptName(font) as String

let text = try! String(contentsOfFile: args[2], encoding: .utf8)
var out = ""
for line in text.split(separator: "\n", omittingEmptySubsequences: false) {
    let attr = NSAttributedString(string: String(line),
                                  attributes: [NSAttributedString.Key(kCTFontAttributeName as String): font])
    let ctLine = CTLineCreateWithAttributedString(attr)
    var tokens: [String] = []
    for run in CTLineGetGlyphRuns(ctLine) as! [CTRun] {
        let n = CTRunGetGlyphCount(run)
        var glyphs = [CGGlyph](repeating: 0, count: n)
        var pos = [CGPoint](repeating: .zero, count: n)
        CTRunGetGlyphs(run, CFRange(location: 0, length: 0), &glyphs)
        CTRunGetPositions(run, CFRange(location: 0, length: 0), &pos)
        let runFont = (CTRunGetAttributes(run) as NSDictionary)[kCTFontAttributeName] as! CTFont
        let fallback = (CTFontCopyPostScriptName(runFont) as String) == name ? "" : "!"
        for i in 0..<n {
            tokens.append("\(glyphs[i]):\(Int(pos[i].x.rounded())):\(Int(pos[i].y.rounded()))\(fallback)")
        }
    }
    out += tokens.joined(separator: " ") + "\n"
}
FileHandle.standardOutput.write(out.data(using: .utf8)!)
