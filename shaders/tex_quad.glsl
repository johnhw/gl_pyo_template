#version 330

#if defined VERTEX_SHADER

in vec3 in_position;
in vec2 in_texcoord_0;

uniform mat4 m_model;
uniform mat4 m_camera;
uniform mat4 m_proj;

out vec2 texCoord;

// Standard modelview-projection transform
void main() {
    mat4 m_view = m_camera * m_model;
    vec4 p = m_view * vec4(in_position, 1.0);
    gl_Position =  m_proj * p;    
    texCoord = in_texcoord_0;

}

#elif defined FRAGMENT_SHADER

uniform sampler2D tex;  // texture to render
uniform float iTime;    // time in seconds
in vec2 texCoord;       // UV coords
out vec4 fragColor;     // output RGBA

void main() {
    vec2 tc = texCoord - vec2(0.5, 0.5);
    float delta = 0.004;
    // thin border
    float border = smoothstep(0.5-delta, 0.5, max(abs(tc.x),abs(tc.y)));            
    vec4 border_color = vec4(1.0, 1.0, 1.0, 1.0);
    // fade in the drawing
    float time_fade_in = smoothstep(0.0, 0.5, iTime);
    vec4 color = border * border_color + (1.0-border) * texture(tex, texCoord);    
    fragColor = color * time_fade_in;
}
#endif
