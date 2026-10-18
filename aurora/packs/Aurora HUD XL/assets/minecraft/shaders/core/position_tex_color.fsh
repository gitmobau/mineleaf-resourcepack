#version 330
#extension GL_ARB_separate_shader_objects : require

// Can't moj_import in things used during startup, when resource packs don't exist.
// This is a copy of dynamicimports.glsl
layout(std140) uniform DynamicTransforms {
    mat4 ModelViewMat;
    mat4 TextureMat;
    vec4 ColorModulator;
    vec3 ModelOffset;
};

uniform sampler2D Sampler0;

layout(location = 0) in vec2 texCoord0;
layout(location = 1) in vec4 vertexColor;

layout(location = 0) out vec4 fragColor;

// Aurora HUD XL: corner marker / shift texels (see position_tex_color.vsh) are replaced by the texel
// next to them (below for top corners, above for bottom ones); in HUD sprites that one is empty -> discarded.
const int MARK = 167;
const int SHIFT = 168;

void main() {
    vec4 tex = texture(Sampler0, texCoord0);
    ivec4 m = ivec4(round(tex * 255.0));
    if ((m.b == MARK || m.b == SHIFT) && m.a >= 1 && m.a <= 4) {
        tex = texture(Sampler0, texCoord0 + vec2(0.0, m.a <= 2 ? 1.0 : -1.0) / vec2(textureSize(Sampler0, 0)));
    }
    vec4 color = tex * vertexColor;
    if (color.a == 0.0) {
        discard;
    }
    fragColor = color * ColorModulator;
}
