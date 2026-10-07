#version 330
#extension GL_ARB_separate_shader_objects : require

#include <minecraft:fog.glsl>
#include <minecraft:dynamictransforms.glsl>
#include <minecraft:oit.glsl>

layout(location = 0) in float sphericalVertexDistance;
layout(location = 1) in float cylindricalVertexDistance;
layout(location = 2) in vec4 vertexColor;
layout(location = 3) in float lineSide;
layout(location = 4) flat in float isOutline;

#ifndef OIT_ALPHA_ONLY
layout(location = 0) out vec4 fragColor;
#endif

vec4 calculateFinalColor(vec4 color) {
    #ifdef OIT_ACCUMULATE
    color = sampleColorForAccumulation(color);
    vec4 fogColor = vec4(FogColor.rgb * color.a, FogColor.a);
    #else
    vec4 fogColor = FogColor;
    #endif
    return apply_fog(color, sphericalVertexDistance, cylindricalVertexDistance, FogEnvironmentalStart, FogEnvironmentalEnd, FogRenderDistanceStart, FogRenderDistanceEnd, fogColor);
}

// Aurora neon: white-hot core fading into a soft aurora-coloured glow.
vec4 auroraNeon(vec4 base) {
    float d = clamp(abs(lineSide), 0.0, 1.0);
    float core = 1.0 - smoothstep(0.22, 0.36, d);
    float glow = pow(1.0 - d, 1.6) * 0.9;
    vec3 coreColor = mix(vec3(1.0), base.rgb, 0.55);
    vec3 rgb = mix(base.rgb, coreColor, core);
    float a = max(core, glow);
    if (a < 0.01) {
        discard;
    }
    return vec4(rgb, a);
}

void main() {
    vec4 base = vertexColor;
    if (isOutline > 0.5) {
        base = auroraNeon(base);
    }
    vec4 color = base * ColorModulator;
    #ifdef OIT_ALPHA_ONLY
    executeAlphaOnlyPhase(gl_FragCoord.z, color.a);
    #else
    fragColor = calculateFinalColor(color);
    #endif
}
