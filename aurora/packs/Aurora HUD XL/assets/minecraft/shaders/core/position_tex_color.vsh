#version 330
#extension GL_ARB_separate_shader_objects : require

// Can't moj_import in things used during startup, when resource packs don't exist.
// This is a copy of dynamicimports.glsl and projection.glsl
layout(std140) uniform DynamicTransforms {
    mat4 ModelViewMat;
    mat4 TextureMat;
    vec4 ColorModulator;
    vec3 ModelOffset;
};
layout(std140) uniform Projection {
    mat4 ProjMat;
};

uniform sampler2D Sampler0;

layout(location = 0) in vec3 Position;
layout(location = 1) in vec2 UV0;
layout(location = 2) in vec4 Color;

layout(location = 0) out vec2 texCoord0;
layout(location = 1) out vec4 vertexColor;

// Aurora HUD XL: sprites that carry corner markers grow past their vanilla rectangle.
// Marker texel = (pad_x, pad_y, 167, role), role 1..4 = top-left, top-right, bottom-left, bottom-right.
// GUI quads are emitted top-left, bottom-left, bottom-right, top-right, so each vertex knows its corner and
// reads only the texel just inside that corner of its own sprite (never a neighbour in the atlas). If it is
// the marker of that corner, the vertex moves out by the pads. The texture already holds the bigger art.
const int MARK = 167;
const int ROLE[4] = int[](1, 3, 4, 2);

void main() {
    vec3 pos = Position;
    // GUI orthographic projection: ProjMat[1][1] = -2 / guiHeight. Only the bottom HUD strip is considered.
    float guiHeight = 2.0 / max(abs(ProjMat[1][1]), 1e-6);
    if (pos.y > guiHeight - 40.0) {
        int role = ROLE[gl_VertexIndex % 4];
        vec2 inward = vec2(role == 1 || role == 3 ? 1.0 : -1.0, role <= 2 ? 1.0 : -1.0);
        vec2 halfTexel = 0.5 / vec2(textureSize(Sampler0, 0));
        ivec4 m = ivec4(round(textureLod(Sampler0, UV0 + inward * halfTexel, 0.0) * 255.0));
        if (m.b == MARK && m.a == role) {
            pos.xy -= inward * vec2(m.rg);
        }
    }
    gl_Position = ProjMat * ModelViewMat * vec4(pos, 1.0);

    texCoord0 = UV0;
    vertexColor = Color;
}
