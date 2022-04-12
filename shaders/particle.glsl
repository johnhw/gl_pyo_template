#version 330

#if defined VERTEX_SHADER

in vec4 in_position;



out vec3 vpos;

void main() {    
    vec4 p = in_position + vec4(0.0,0.0,0.0,0.0); 
    vpos = p.xyz;
    gl_Position =  p;
}

// construct the 2-triangles
// quads from each input point
// aligned to face the camera

#elif defined GEOMETRY_SHADER

layout( points ) in;
layout( triangle_strip, max_vertices = 4 ) out;
out vec2 texCoord;
in vec3 vpos[1];
out vec3 gpos;

// generate micro quads for each point
void main()
{
    float d = 0.006;
    gpos = vpos[0];
    vec3 pos = gl_in[0].gl_Position.xyz;
    
    vec3 up = (vec4(0.0, d, 0.0, 0.0)).xyz;
    vec3 right = (vec4(d, 0.0, 0.0, 0.0)).xyz;

    gl_Position = vec4(pos - up - right, 1.0);
    texCoord = vec2(0.0, 0.0);
    EmitVertex();

    gl_Position = vec4(pos - up + right, 1.0);
    texCoord = vec2(1.0, 0.0);
    EmitVertex();
    
    gl_Position = vec4(pos + up - right, 1.0);
    texCoord = vec2(0.0, 1.0);
    EmitVertex();
    
    gl_Position = vec4(pos + up + right, 1.0);
    texCoord = vec2(1.0, 1.0);
    EmitVertex();

   EndPrimitive();
}


#elif defined FRAGMENT_SHADER

in vec4 position;
in vec2 texCoord;
in vec3 gpos;
out vec4 fragColor;


void main() {
    
    // colour the point with a vertical stripe
    float tc = max(0, 1.0-2*length((texCoord-vec2(0.5, 0.5))*vec2(3.0, 1.0)));
    // fade out at top and bottom
    float fade = 1.0/(1.0+length(gpos.y*3.0));
    //fragColor = vec4(1.0, 1.0, 1.0, 1.0);
    fragColor = vec4(1.0, 1.0, 1.0, tc*0.4*fade);
}
#endif




